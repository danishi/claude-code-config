import AVFoundation
import CoreMedia
import Foundation
import ImageIO
import UniformTypeIdentifiers

// usage: swift pair_live_photo.swift in.jpg in.mov out.jpg out.mov stillSeconds
let a = CommandLine.arguments
guard a.count == 6, let stillSec = Double(a[5]) else {
    print("usage: makelive in.jpg in.mov out.jpg out.mov stillSeconds"); exit(2)
}
let inJPG = URL(fileURLWithPath: a[1]), inMOV = URL(fileURLWithPath: a[2])
let outJPG = URL(fileURLWithPath: a[3]), outMOV = URL(fileURLWithPath: a[4])
let assetID = UUID().uuidString

// ---- 1. JPEG: Apple MakerNote key 17 = content identifier
guard let src = CGImageSourceCreateWithURL(inJPG as CFURL, nil),
      let dst = CGImageDestinationCreateWithURL(outJPG as CFURL, UTType.jpeg.identifier as CFString, 1, nil)
else { print("jpeg open failed"); exit(1) }
var props = (CGImageSourceCopyPropertiesAtIndex(src, 0, nil) as? [String: Any]) ?? [:]
props[kCGImagePropertyMakerAppleDictionary as String] = ["17": assetID]
props[kCGImageDestinationLossyCompressionQuality as String] = 0.95
CGImageDestinationAddImageFromSource(dst, src, 0, props as CFDictionary)
guard CGImageDestinationFinalize(dst) else { print("jpeg write failed"); exit(1) }

// ---- 2. MOV: content identifier + still-image-time timed metadata track
try? FileManager.default.removeItem(at: outMOV)
let asset = AVURLAsset(url: inMOV)
let reader = try AVAssetReader(asset: asset)
let writer = try AVAssetWriter(outputURL: outMOV, fileType: .mov)

let idItem = AVMutableMetadataItem()
idItem.keySpace = .quickTimeMetadata
idItem.key = "com.apple.quicktime.content.identifier" as NSString
idItem.value = assetID as NSString
idItem.dataType = "com.apple.metadata.datatype.UTF-8"
writer.metadata = [idItem]

var pairs: [(AVAssetReaderTrackOutput, AVAssetWriterInput)] = []
for track in asset.tracks where track.mediaType == .video || track.mediaType == .audio {
    let out = AVAssetReaderTrackOutput(track: track, outputSettings: nil)
    reader.add(out)
    let hint = track.formatDescriptions.first.map { $0 as! CMFormatDescription }
    let inp = AVAssetWriterInput(mediaType: track.mediaType, outputSettings: nil, sourceFormatHint: hint)
    inp.expectsMediaDataInRealTime = false
    if track.mediaType == .video { inp.transform = track.preferredTransform }
    writer.add(inp)
    pairs.append((out, inp))
}

let spec: [String: Any] = [
    kCMMetadataFormatDescriptionMetadataSpecificationKey_Identifier as String:
        "mdta/com.apple.quicktime.still-image-time",
    kCMMetadataFormatDescriptionMetadataSpecificationKey_DataType as String:
        "com.apple.metadata.datatype.int8",
]
var mdesc: CMFormatDescription?
CMMetadataFormatDescriptionCreateWithMetadataSpecifications(
    allocator: kCFAllocatorDefault, metadataType: kCMMetadataFormatType_Boxed,
    metadataSpecifications: [spec] as CFArray, formatDescriptionOut: &mdesc)
let metaInput = AVAssetWriterInput(mediaType: .metadata, outputSettings: nil, sourceFormatHint: mdesc)
let adaptor = AVAssetWriterInputMetadataAdaptor(assetWriterInput: metaInput)
writer.add(metaInput)

guard writer.startWriting() else { print("startWriting: \(String(describing: writer.error))"); exit(1) }
guard reader.startReading() else { print("startReading: \(String(describing: reader.error))"); exit(1) }
writer.startSession(atSourceTime: .zero)

let stillItem = AVMutableMetadataItem()
stillItem.keySpace = .quickTimeMetadata
stillItem.key = "com.apple.quicktime.still-image-time" as NSString
stillItem.value = 0 as NSNumber
stillItem.dataType = "com.apple.metadata.datatype.int8"
let stillRange = CMTimeRange(start: CMTime(seconds: stillSec, preferredTimescale: 600),
                             duration: CMTime(value: 20, timescale: 600))
adaptor.append(AVTimedMetadataGroup(items: [stillItem], timeRange: stillRange))
metaInput.markAsFinished()

let group = DispatchGroup()
for (i, (out, inp)) in pairs.enumerated() {
    group.enter()
    inp.requestMediaDataWhenReady(on: DispatchQueue(label: "q\(i)")) {
        while inp.isReadyForMoreMediaData {
            if let s = out.copyNextSampleBuffer() {
                if !inp.append(s) { print("append failed: \(String(describing: writer.error))"); exit(1) }
            } else {
                inp.markAsFinished(); group.leave(); return
            }
        }
    }
}
group.wait()
let sem = DispatchSemaphore(value: 0)
writer.finishWriting { sem.signal() }
sem.wait()
guard writer.status == .completed else { print("writer: \(String(describing: writer.error))"); exit(1) }
print("OK assetIdentifier=\(assetID)")
