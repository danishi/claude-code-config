import AVFoundation
import CoreMedia
import Foundation
import ImageIO
import UniformTypeIdentifiers
import VideoToolbox

// Build an iPhone Live Photo pair (HEIC + MOV) that iOS accepts as a moving lock screen wallpaper.
//
// usage: swift pair_live_photo.swift in.mov outBase stillSeconds [--no-interp]
//   in.mov        trimmed clip (any codec / frame rate AVFoundation can read)
//   outBase       output path without extension; writes outBase.HEIC and outBase.MOV
//   stillSeconds  key photo time, counted from the start of in.mov
//   --no-interp   repeat frames instead of interpolating them when raising the frame rate
//
// What iOS checks (found by testing on an iPhone, not documented by Apple):
//   - HEIC cover and MOV share one content identifier (MakerApple key 17 / content.identifier)
//   - HEVC video at a constant 60 fps; the cover is the decoded frame at the still time
//   - a live-photo-info timed metadata track whose setup data carries a 'dims' box,
//     linked to the video track with cdsc/cdep references
//   - a still-image-time track (value -1) with a live-photo-still-image-transform

let args = CommandLine.arguments
guard args.count >= 4, let stillArg = Double(args[3]) else {
    print("usage: swift pair_live_photo.swift in.mov outBase stillSeconds [--no-interp]"); exit(2)
}
let inURL = URL(fileURLWithPath: args[1])
let outMOV = URL(fileURLWithPath: args[2] + ".MOV"), outHEIC = URL(fileURLWithPath: args[2] + ".HEIC")
let interpolate = !args.contains("--no-interp")
let fps: Int32 = 60
let tick: CMTimeValue = 10                         // one 60 fps frame at timescale 600
let assetID = UUID().uuidString

func fail(_ msg: String) -> Never { FileHandle.standardError.write(Data((msg + "\n").utf8)); exit(1) }

let asset = AVURLAsset(url: inURL)
guard let srcVideo = asset.tracks(withMediaType: .video).first else { fail("no video track") }
// Frames are written as decoded, so the source must not rely on a rotation transform (ffmpeg re-encodes upright).
guard srcVideo.preferredTransform.isIdentity else { fail("rotated source: re-encode it with ffmpeg first (make_live_photo.sh does this)") }
let width = Int(srcVideo.naturalSize.width), height = Int(srcVideo.naturalSize.height)
let duration = srcVideo.timeRange.duration.seconds
let frameCount = Int((duration * Double(fps)).rounded(.down))
guard frameCount > 1 else { fail("clip is too short") }
let stillFrame = min(max(Int((stillArg * Double(fps)).rounded()), 0), frameCount - 1)
let stillTime = CMTime(value: CMTimeValue(stillFrame) * tick, timescale: 600)

// ---- frame source: decoded frames, optionally interpolated with VideoToolbox
final class FrameSource {
    let output: AVAssetReaderTrackOutput
    var cur: (CVPixelBuffer, Double)?
    var next: (CVPixelBuffer, Double)?
    var processor: AnyObject?          // VTFrameProcessor when interpolation is available
    var pool: CVPixelBufferPool?
    var srcPool: CVPixelBufferPool?
    var copier: VTPixelTransferSession?
    let origin: Double

    init(reader: AVAssetReader, track: AVAssetTrack, interpolate: Bool, width: Int, height: Int) {
        var settings: [String: Any] = [kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
                                       kCVPixelBufferIOSurfacePropertiesKey as String: [String: Any]()]
        if interpolate, #available(macOS 15.4, *), VTFrameRateConversionConfiguration.isSupported,
           let cfg = VTFrameRateConversionConfiguration(frameWidth: width, frameHeight: height, usePrecomputedFlow: false,
                                                        qualityPrioritization: .quality, revision: VTFrameRateConversionConfiguration.defaultRevision) {
            let p = VTFrameProcessor()
            do {
                try p.startSession(configuration: cfg)
                processor = p
                settings = cfg.sourcePixelBufferAttributes
                CVPixelBufferPoolCreate(nil, nil, cfg.destinationPixelBufferAttributes as CFDictionary, &pool)
                CVPixelBufferPoolCreate(nil, nil, cfg.sourcePixelBufferAttributes as CFDictionary, &srcPool)
                VTPixelTransferSessionCreate(allocator: nil, pixelTransferSessionOut: &copier)
            } catch { FileHandle.standardError.write(Data("interpolation unavailable, repeating frames: \(error)\n".utf8)) }
        }
        output = AVAssetReaderTrackOutput(track: track, outputSettings: settings)
        output.alwaysCopiesSampleData = false
        reader.add(output)
        origin = track.timeRange.start.seconds
    }

    private func read() -> (CVPixelBuffer, Double)? {
        while let s = output.copyNextSampleBuffer() {
            guard let pb = CMSampleBufferGetImageBuffer(s) else { continue }
            let t = CMSampleBufferGetPresentationTimeStamp(s).seconds - origin
            // Copy decoded frames into our own buffers so the reader's pool is never held by the interpolator.
            if let srcPool, let copier {
                var copy: CVPixelBuffer?
                CVPixelBufferPoolCreatePixelBuffer(nil, srcPool, &copy)
                if let copy, VTPixelTransferSessionTransferImage(copier, from: pb, to: copy) == noErr { return (copy, t) }
            }
            return (pb, t)
        }
        return nil
    }

    /// Frame to show at time t (seconds from clip start).
    func frame(at t: Double) -> CVPixelBuffer {
        if cur == nil { cur = read(); next = read() }
        while let n = next, n.1 <= t + 1e-4 { cur = n; next = read() }
        guard let c = cur else { fail("no decodable frames") }
        guard let n = next else { return c.0 }
        let phase = (t - c.1) / (n.1 - c.1)
        if phase < 0.02 { return c.0 }
        if phase > 0.98 { return n.0 }
        if #available(macOS 15.4, *), let p = processor as? VTFrameProcessor, let pool {
            var dst: CVPixelBuffer?
            CVPixelBufferPoolCreatePixelBuffer(nil, pool, &dst)
            let pts = CMTime(seconds: t, preferredTimescale: 600)
            if let dst,
               let src = VTFrameProcessorFrame(buffer: c.0, presentationTimeStamp: CMTime(seconds: c.1, preferredTimescale: 600)),
               let nxt = VTFrameProcessorFrame(buffer: n.0, presentationTimeStamp: CMTime(seconds: n.1, preferredTimescale: 600)),
               let out = VTFrameProcessorFrame(buffer: dst, presentationTimeStamp: pts),
               let params = VTFrameRateConversionParameters(sourceFrame: src, nextFrame: nxt, opticalFlow: nil,
                                                            interpolationPhase: [Float(phase)], submissionMode: .random,
                                                            destinationFrames: [out]) {
                let sem = DispatchSemaphore(value: 0)
                var failure: Error?
                p.process(parameters: params) { _, err in failure = err; sem.signal() }
                sem.wait()
                if failure == nil { return dst }
                FileHandle.standardError.write(Data("interpolation failed, repeating frames: \(failure!)\n".utf8))
                processor = nil
            }
        }
        return phase < 0.5 ? c.0 : n.0
    }
}

// ---- writer
let reader = try AVAssetReader(asset: asset)
let source = FrameSource(reader: reader, track: srcVideo, interpolate: interpolate, width: width, height: height)
let audioTrack = asset.tracks(withMediaType: .audio).first
var audioOut: AVAssetReaderTrackOutput?
if let audioTrack {
    let o = AVAssetReaderTrackOutput(track: audioTrack, outputSettings: nil)
    reader.add(o); audioOut = o
}

try? FileManager.default.removeItem(at: outMOV)
let writer = try AVAssetWriter(outputURL: outMOV, fileType: .mov)
writer.movieTimeScale = 600

func item(_ key: String, _ value: NSObject & NSCopying, _ type: String) -> AVMetadataItem {
    let i = AVMutableMetadataItem()
    i.keySpace = .quickTimeMetadata; i.key = key as NSString; i.value = value; i.dataType = type
    return i
}
writer.metadata = [
    item("com.apple.quicktime.content.identifier", assetID as NSString, "com.apple.metadata.datatype.UTF-8"),
    item("com.apple.quicktime.live-photo.auto", NSNumber(value: UInt8(1)), "com.apple.metadata.datatype.uint8"),
    item("com.apple.quicktime.live-photo.vitality-score", NSNumber(value: Float(1)), "com.apple.metadata.datatype.float32"),
    item("com.apple.quicktime.live-photo.vitality-scoring-version", NSNumber(value: Int64(4)), "com.apple.metadata.datatype.int64"),
    item("com.apple.quicktime.full-frame-rate-playback-intent", NSNumber(value: Int64(1)), "com.apple.metadata.datatype.int64"),
]

let videoIn = AVAssetWriterInput(mediaType: .video, outputSettings: [
    AVVideoCodecKey: AVVideoCodecType.hevc, AVVideoWidthKey: width, AVVideoHeightKey: height,
    AVVideoCompressionPropertiesKey: [AVVideoAverageBitRateKey: 16_000_000, AVVideoExpectedSourceFrameRateKey: fps,
                                      AVVideoMaxKeyFrameIntervalKey: fps,
                                      AVVideoProfileLevelKey: kVTProfileLevel_HEVC_Main_AutoLevel as String]])
videoIn.expectsMediaDataInRealTime = false
videoIn.mediaTimeScale = 600
let adaptor = AVAssetWriterInputPixelBufferAdaptor(assetWriterInput: videoIn, sourcePixelBufferAttributes: [
    kCVPixelBufferPixelFormatTypeKey as String: kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange,
    kCVPixelBufferWidthKey as String: width, kCVPixelBufferHeightKey as String: height,
    kCVPixelBufferIOSurfacePropertiesKey as String: [String: Any]()])
// The interpolator works in 16-bit RGBA; hand the encoder plain 8-bit YUV frames.
var transfer: VTPixelTransferSession?
VTPixelTransferSessionCreate(allocator: nil, pixelTransferSessionOut: &transfer)
func encoderFrame(_ pb: CVPixelBuffer) -> CVPixelBuffer {
    if CVPixelBufferGetPixelFormatType(pb) == kCVPixelFormatType_420YpCbCr8BiPlanarVideoRange { return pb }
    guard let pool = adaptor.pixelBufferPool, let transfer else { fail("no pixel buffer pool") }
    var out: CVPixelBuffer?
    CVPixelBufferPoolCreatePixelBuffer(nil, pool, &out)
    guard let out, VTPixelTransferSessionTransferImage(transfer, from: pb, to: out) == noErr else { fail("pixel transfer failed") }
    return out
}
writer.add(videoIn)

var audioIn: AVAssetWriterInput?
if let audioTrack {
    let hint = audioTrack.formatDescriptions.first.map { $0 as! CMFormatDescription }
    let i = AVAssetWriterInput(mediaType: .audio, outputSettings: nil, sourceFormatHint: hint)
    i.expectsMediaDataInRealTime = false
    writer.add(i); audioIn = i
}

// ---- Live Photo metadata tracks
func be32(_ v: UInt32) -> Data { withUnsafeBytes(of: v.bigEndian) { Data($0) } }
func beF64(_ v: Double) -> Data { withUnsafeBytes(of: v.bitPattern.bigEndian) { Data($0) } }
func box(_ kind: String, _ body: Data) -> Data { be32(UInt32(8 + body.count)) + Data(kind.utf8) + body }
func boxed(_ localID: UInt32, _ value: Data) -> Data { be32(UInt32(8 + value.count)) + be32(localID) + value }

// Setup data = 'cfgv' (binary plist) + 'dims' (video width/height). Without 'dims' iOS refuses wallpaper motion.
let setupPlist: [String: Any] = [
    "LivePhotoMetadataSetupDataVersion": 1,
    "SystemVersion": ["ProductBuildVersion": "23B85", "ProductName": "iPhone OS", "ProductVersion": "26.1"],
    "FrameworkVersions": ["CoreMotion": "3060.0.18.0.4", "CMCaptureCore": "664.42.7.0.1", "H16ISPServices": "4.109", "CoreMedia": "3285.11.1.4"],
]
let setup = box("cfgv", try PropertyListSerialization.data(fromPropertyList: setupPlist, format: .binary, options: 0))
    + box("dims", be32(UInt32(width)) + be32(UInt32(height)))

let infoType = "com.apple.quicktime.com.apple.quicktime.live-photo-info"
CMMetadataDataTypeRegistryRegisterDataType(infoType as CFString, description: "Live Photo info" as CFString,
                                           conformingDataTypes: [kCMMetadataBaseDataType_RawData] as CFArray)
func metadataFormat(_ specs: [[String: Any]]) -> CMFormatDescription {
    var fd: CMFormatDescription?
    let st = CMMetadataFormatDescriptionCreateWithMetadataSpecifications(allocator: kCFAllocatorDefault,
        metadataType: kCMMetadataFormatType_Boxed, metadataSpecifications: specs as CFArray, formatDescriptionOut: &fd)
    guard st == noErr, let fd else { fail("metadata format \(st)") }
    return fd
}
let K = kCMMetadataFormatDescriptionMetadataSpecificationKey_Identifier as String
let D = kCMMetadataFormatDescriptionMetadataSpecificationKey_DataType as String
let infoFD = metadataFormat([[K: "mdta/com.apple.quicktime.live-photo-info", D: infoType,
                              kCMMetadataFormatDescriptionMetadataSpecificationKey_SetupData as String: setup]])
let stillFD = metadataFormat([
    [K: "mdta/com.apple.quicktime.still-image-time", D: kCMMetadataBaseDataType_SInt8 as String],
    [K: "mdta/com.apple.quicktime.live-photo-still-image-transform", D: kCMMetadataBaseDataType_PerspectiveTransformF64 as String],
])
let infoIn = AVAssetWriterInput(mediaType: .metadata, outputSettings: nil, sourceFormatHint: infoFD)
let stillIn = AVAssetWriterInput(mediaType: .metadata, outputSettings: nil, sourceFormatHint: stillFD)
for i in [infoIn, stillIn] { i.expectsMediaDataInRealTime = false; i.mediaTimeScale = 600; writer.add(i) }
let cdsc = AVAssetTrack.AssociationType.metadataReferent.rawValue
infoIn.addTrackAssociation(withTrackOf: videoIn, type: cdsc)
infoIn.addTrackAssociation(withTrackOf: videoIn, type: "cdep")
stillIn.addTrackAssociation(withTrackOf: videoIn, type: cdsc)

func metadataSample(_ bytes: Data, _ fd: CMFormatDescription, _ t: CMTime, _ d: CMTime) -> CMSampleBuffer {
    var bb: CMBlockBuffer?
    CMBlockBufferCreateWithMemoryBlock(allocator: kCFAllocatorDefault, memoryBlock: nil, blockLength: bytes.count,
        blockAllocator: kCFAllocatorDefault, customBlockSource: nil, offsetToData: 0, dataLength: bytes.count,
        flags: kCMBlockBufferAssureMemoryNowFlag, blockBufferOut: &bb)
    bytes.withUnsafeBytes { _ = CMBlockBufferReplaceDataBytes(with: $0.baseAddress!, blockBuffer: bb!, offsetIntoDestination: 0, dataLength: bytes.count) }
    var timing = CMSampleTimingInfo(duration: d, presentationTimeStamp: t, decodeTimeStamp: .invalid)
    var sampleSize = bytes.count
    var sb: CMSampleBuffer?
    CMSampleBufferCreate(allocator: kCFAllocatorDefault, dataBuffer: bb, dataReady: true, makeDataReadyCallback: nil,
        refcon: nil, formatDescription: fd, sampleCount: 1, sampleTimingEntryCount: 1, sampleTimingArray: &timing,
        sampleSizeEntryCount: 1, sampleSizeArray: &sampleSize, sampleBufferOut: &sb)
    return sb!
}
let frameDur = CMTime(value: tick, timescale: 600)
// One live-photo-info sample per frame. The camera stores motion data here; zeros are accepted.
let infoPayload = boxed(1, Data(count: 136))
var identity = Data(); for v in [1.0, 0, 0, 0, 1, 0, 0, 0, 1] { identity += beF64(v) }
let stillSample = metadataSample(boxed(1, Data([0xFF])) + boxed(2, identity), stillFD, stillTime, CMTime(value: 1, timescale: 600))

// Frameworks may call back on the main queue, so do the blocking work on a background thread.
func writeAll() throws {
    guard writer.startWriting() else { fail("startWriting: \(String(describing: writer.error))") }
    guard reader.startReading() else { fail("startReading: \(String(describing: reader.error))") }
    writer.startSession(atSourceTime: .zero)

    let endTime = CMTime(value: CMTimeValue(frameCount) * tick, timescale: 600)
    // The writer interleaves tracks and may hold back video until it has audio for the same span,
    // so whenever an input is not ready, feed it the next audio sample (audio is passed through as is).
    // Audio is shifted by the same origin as the video so both start at zero.
    func nextAudio() -> CMSampleBuffer? {
        guard let s = audioOut?.copyNextSampleBuffer() else { return nil }
        if source.origin == 0 { return s }
        var timing = CMSampleTimingInfo()
        CMSampleBufferGetSampleTimingInfo(s, at: 0, timingInfoOut: &timing)
        let shift = CMTime(seconds: source.origin, preferredTimescale: 600)
        timing.presentationTimeStamp = timing.presentationTimeStamp - shift
        timing.decodeTimeStamp = .invalid
        var out: CMSampleBuffer?
        CMSampleBufferCreateCopyWithNewTiming(allocator: nil, sampleBuffer: s, sampleTimingEntryCount: 1, sampleTimingArray: &timing, sampleBufferOut: &out)
        return out
    }
    var pendingAudio: CMSampleBuffer? = nextAudio()
    if pendingAudio == nil { audioIn?.markAsFinished() }
    func pumpAudio() -> Bool {
        guard let audioIn, let s = pendingAudio else { return false }
        if CMSampleBufferGetPresentationTimeStamp(s) >= endTime {
            pendingAudio = nil; audioIn.markAsFinished(); return false
        }
        guard audioIn.isReadyForMoreMediaData else { return false }
        guard audioIn.append(s) else { fail("audio append: \(String(describing: writer.error))") }
        pendingAudio = nextAudio()
        if pendingAudio == nil { audioIn.markAsFinished() }
        return true
    }
    func waitReady(_ i: AVAssetWriterInput) {
        while !i.isReadyForMoreMediaData { if !pumpAudio() { usleep(2000) } }
    }

    // The still track holds a single sample; write it and finish the input so the writer never waits on it.
    waitReady(stillIn)
    guard stillIn.append(stillSample) else { fail("still append: \(String(describing: writer.error))") }
    stillIn.markAsFinished()

    // Video and its per-frame info samples, written in step.
    for n in 0..<frameCount {
        let t = CMTime(value: CMTimeValue(n) * tick, timescale: 600)
        let pb = encoderFrame(source.frame(at: Double(n) / Double(fps)))
        waitReady(videoIn)
        guard adaptor.append(pb, withPresentationTime: t) else { fail("video append: \(String(describing: writer.error))") }
        waitReady(infoIn)
        guard infoIn.append(metadataSample(infoPayload, infoFD, t, frameDur)) else { fail("info append: \(String(describing: writer.error))") }
    }
    videoIn.markAsFinished(); infoIn.markAsFinished()
    while pendingAudio != nil { if !pumpAudio() { usleep(2000) } }
    reader.cancelReading()
    writer.endSession(atSourceTime: endTime)
    let done = DispatchSemaphore(value: 0)
    writer.finishWriting { done.signal() }
    done.wait()
    guard writer.status == .completed else { fail("writer: \(String(describing: writer.error))") }

    // ---- cover: the decoded output frame at the still time, as HEIC with the shared identifier
    let generator = AVAssetImageGenerator(asset: AVURLAsset(url: outMOV))
    generator.requestedTimeToleranceBefore = .zero
    generator.requestedTimeToleranceAfter = .zero
    generator.appliesPreferredTrackTransform = true
    let cover = try generator.copyCGImage(at: stillTime, actualTime: nil)
    guard let dst = CGImageDestinationCreateWithURL(outHEIC as CFURL, UTType.heic.identifier as CFString, 1, nil) else { fail("heic open") }
    CGImageDestinationAddImage(dst, cover, [kCGImagePropertyMakerAppleDictionary as String: ["17": assetID],
                                            kCGImageDestinationLossyCompressionQuality as String: 0.92] as CFDictionary)
    guard CGImageDestinationFinalize(dst) else { fail("heic write") }
    print("OK \(assetID) \(width)x\(height) \(frameCount) frames, still at \(Double(stillFrame) / Double(fps))s")
}

DispatchQueue.global(qos: .userInitiated).async {
    do { try writeAll(); exit(0) } catch { fail("\(error)") }
}
dispatchMain()
