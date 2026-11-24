#!/usr/bin/env node
// シェーダーをヘッドレスChromiumで1枚ずつ描いてPNG（無劣化）に書き出す。GPUがあれば使い、無ければSwiftShader。
// 使い方:
//   node render.js config.json --out work/frames                 全フレーム（既存フレームは飛ばすので再開できる）
//   node render.js config.json --out work/prev --frames 0,60,120 指定フレームだけ（プレビュー用）
//   オプション: --from N --to N / --scale 0.5（プレビューを速くする）/ --budget 秒（時間で区切って終了）
const fs = require('fs'), path = require('path'), cp = require('child_process');

function loadPlaywright() {
  try { return require('playwright'); } catch (e) {}
  const root = cp.execSync('npm root -g').toString().trim();
  return require(path.join(root, 'playwright'));
}
function findChrome() {
  const base = '/opt/pw-browsers';
  if (fs.existsSync(base)) {
    for (const d of fs.readdirSync(base).filter(d => /^chromium-\d+/.test(d)).sort().reverse()) {
      for (const sub of ['chrome-linux64/chrome', 'chrome-linux/chrome']) {
        const p = path.join(base, d, sub);
        if (fs.existsSync(p)) return p;
      }
    }
  }
  return undefined; // Playwright既定のブラウザに任せる
}
function merge(a, b) {
  const o = { ...a };
  for (const k of Object.keys(b || {})) o[k] = (b[k] && typeof b[k] === 'object' && !Array.isArray(b[k])) ? merge(a[k] || {}, b[k]) : b[k];
  return o;
}
function arg(name, def) { const i = process.argv.indexOf('--' + name); return i > 0 ? process.argv[i + 1] : def; }

(async () => {
  const here = __dirname;
  const cfgPath = process.argv[2];
  if (!cfgPath) { console.error('usage: node render.js config.json --out DIR [--frames a,b,c] [--from N --to N] [--scale S]'); process.exit(1); }
  const cfg = merge(JSON.parse(fs.readFileSync(path.join(here, 'defaults.json'))), JSON.parse(fs.readFileSync(cfgPath)));
  const pals = JSON.parse(fs.readFileSync(path.join(here, 'palettes.json')));
  const pal = typeof cfg.look.palette === 'string' ? pals[cfg.look.palette] : cfg.look.palette;
  if (!pal) { console.error('unknown palette: ' + cfg.look.palette + ' (' + Object.keys(pals).join(', ') + ')'); process.exit(1); }
  // 画質プリセット（standard/high/max）を土台に、configのqualityに書かれた値で上書きする
  const preset = cfg.presets[cfg.quality.preset];
  if (!preset) { console.error('unknown quality.preset: ' + cfg.quality.preset + ' (' + Object.keys(cfg.presets).join(', ') + ')'); process.exit(1); }
  cfg.quality = { ...preset, ...cfg.quality };
  cfg.fps = cfg.fps || cfg.quality.fps;   // fpsは最上位に書けばそれが優先、無ければpresetの値
  const scale = parseFloat(arg('scale', '1')) * cfg.quality.scale;
  const W = Math.round(cfg.width * scale / 2) * 2, H = Math.round(cfg.height * scale / 2) * 2;
  const total = Math.round(cfg.duration * cfg.fps);
  const out = arg('out', 'frames'); fs.mkdirSync(out, { recursive: true });
  let list;
  if (arg('frames')) list = arg('frames').split(',').map(Number);
  else { const a = parseInt(arg('from', '0')), b = parseInt(arg('to', String(total))); list = []; for (let f = a; f < b; f++) list.push(f); }
  // シーンは scenes/ の名前か、.glsl ファイルへのパス（configからの相対も可）
  let scenePath = [path.join(here, 'scenes', cfg.scene + '.glsl'), path.resolve(path.dirname(cfgPath), cfg.scene), cfg.scene].find(p => fs.existsSync(p) && fs.statSync(p).isFile());
  if (!scenePath) { console.error('scene が見つからない: ' + cfg.scene + ' (' + fs.readdirSync(path.join(here, 'scenes')).map(f => f.replace('.glsl', '')).join(', ') + ' か .glsl のパス)'); process.exit(1); }
  const lib = n => fs.readFileSync(path.join(here, 'lib', n), 'utf8');
  const head = '#version 300 es\n' + lib('common.glsl') + '\n' + fs.readFileSync(scenePath, 'utf8') + '\n';
  const sceneSrc = head + lib('main.glsl'), postSrc = head + lib('post.glsl');
  const { chromium } = loadPlaywright();
  const SOFT = ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
  const HARD = ['--enable-gpu', '--ignore-gpu-blocklist', '--enable-webgl'];
  async function open(args) {
    const browser = await chromium.launch({ executablePath: findChrome(), args });
    const page = await browser.newPage({ viewport: { width: W, height: H } });
    page.on('console', m => console.log('[page]', m.text()));
    await page.setContent(`<canvas id="c" width="${W}" height="${H}"></canvas>`);
    const gpu = await page.evaluate(() => {
      const gl = document.createElement('canvas').getContext('webgl2'); if (!gl) return null;
      const e = gl.getExtension('WEBGL_debug_renderer_info'); return e ? gl.getParameter(e.UNMASKED_RENDERER_WEBGL) : 'unknown';
    });
    return { browser, page, gpu };
  }
  // 実機のGPUがあれば使う（数十倍速い）。無ければソフトウェア描画（SwiftShader）に切り替える
  let s0 = null;
  if (!process.argv.includes('--software')) {
    try { s0 = await open(HARD); } catch (e) { s0 = null; }
    if (s0 && (!s0.gpu || /swiftshader|llvmpipe|software/i.test(s0.gpu))) { await s0.browser.close(); s0 = null; }
  }
  if (!s0) s0 = await open(SOFT);
  const { browser, page } = s0;
  console.log('renderer: ' + s0.gpu);
  const info = await page.evaluate(({ sceneSrc, postSrc, W, H, cfg, pal }) => {
    const gl = document.getElementById('c').getContext('webgl2', { preserveDrawingBuffer: true, antialias: false });
    if (!gl) return { error: 'WebGL2が使えない' };
    const hdr = !!gl.getExtension('EXT_color_buffer_float') || !!gl.getExtension('EXT_color_buffer_half_float');
    const vs = `#version 300 es\nin vec2 p;void main(){gl_Position=vec4(p,0.,1.);}`;
    function prog(fsSrc, label) {
      const pr = gl.createProgram();
      for (const [t, s] of [[gl.VERTEX_SHADER, vs], [gl.FRAGMENT_SHADER, fsSrc]]) {
        const sh = gl.createShader(t); gl.shaderSource(sh, s); gl.compileShader(sh);
        if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error(label + ': ' + gl.getShaderInfoLog(sh));
        gl.attachShader(pr, sh);
      }
      gl.bindAttribLocation(pr, 0, 'p'); gl.linkProgram(pr);
      if (!gl.getProgramParameter(pr, gl.LINK_STATUS)) throw new Error(label + ': ' + gl.getProgramInfoLog(pr));
      return pr;
    }
    let scene, post;
    try { scene = prog(sceneSrc, 'scene'); post = prog(postSrc, 'post'); } catch (e) { return { error: String(e.message) }; }
    const buf = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 3, -1, -1, 3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);
    const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
    if (hdr) gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA16F, W, H, 0, gl.RGBA, gl.HALF_FLOAT, null);
    else gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, W, H, 0, gl.RGBA, gl.UNSIGNED_BYTE, null);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
    const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0);
    const L = cfg.look, U = (p, n) => gl.getUniformLocation(p, n);
    const cum = []; let s = 0; const ws = pal.weights, wt = ws.reduce((a, b) => a + b, 0);
    for (const w of ws) { s += w / wt; cum.push(s); }
    const set = (p, vals) => { for (const k in vals) { const l = U(p, k); if (l) gl.uniform1f(l, vals[k]); } };
    const NS = Math.max(1, Math.round(cfg.quality.samples));
    const halton = (i, b) => { let f = 1, r = 0; while (i > 0) { f /= b; r += f * (i % b); i = Math.floor(i / b); } return r; };
    window.renderFrame = (t) => {
      const beat = t * cfg.bpm / 60;
      const common = { uTime: t, uBeat: beat, uSeed: cfg.seed, uSpeed: L.speed, uWarp: L.warp, uFov: L.fov, uRoll: L.roll, uDensity: L.density, uReflect: L.reflect, uPulse: L.pulse };
      gl.viewport(0, 0, W, H);
      // 1パス目：サブピクセルをずらして複数回描き、加算で平均する（輪郭のギザギザを取る）
      gl.bindFramebuffer(gl.FRAMEBUFFER, fb); gl.useProgram(scene);
      gl.clearColor(0, 0, 0, 0); gl.clear(gl.COLOR_BUFFER_BIT);
      gl.enable(gl.BLEND); gl.blendFunc(gl.ONE, gl.ONE);
      gl.uniform2f(U(scene, 'uRes'), W, H); set(scene, common); gl.uniform1f(U(scene, 'uWeight'), 1 / NS);
      gl.uniform3fv(U(scene, 'uPal'), new Float32Array(pal.colors.flat())); gl.uniform1fv(U(scene, 'uPalW'), new Float32Array(cum));
      for (let i = 0; i < NS; i++) {
        gl.uniform2f(U(scene, 'uJitter'), NS > 1 ? halton(i + 1, 2) - 0.5 : 0, NS > 1 ? halton(i + 1, 3) - 0.5 : 0);
        gl.drawArrays(gl.TRIANGLES, 0, 3);
      }
      gl.disable(gl.BLEND);
      // 2パス目：仕上げ
      gl.bindFramebuffer(gl.FRAMEBUFFER, null); gl.bindTexture(gl.TEXTURE_2D, tex); gl.generateMipmap(gl.TEXTURE_2D);
      gl.useProgram(post);
      gl.uniform1i(U(post, 'uScene'), 0); gl.uniform2f(U(post, 'uRes'), W, H); set(post, common);
      gl.uniform3fv(U(post, 'uPal'), new Float32Array(pal.colors.flat())); gl.uniform1fv(U(post, 'uPalW'), new Float32Array(cum));
      set(post, { uExposure: L.exposure, uBloom: L.bloom, uAberr: L.aberration, uSat: L.saturation, uShutter: cfg.quality.shutter, uFps: cfg.fps, uGrain: L.grain, uTaps: cfg.quality.blurTaps });
      gl.drawArrays(gl.TRIANGLES, 0, 3); gl.finish();
      return document.getElementById('c').toDataURL('image/png');
    };
    return { hdr };
  }, { sceneSrc, postSrc, W, H, cfg, pal });
  if (info.error) { console.error('シェーダーエラー: ' + info.error); await browser.close(); process.exit(2); }
  console.log(`scene=${cfg.scene} ${W}x${H} ${cfg.fps}fps preset=${cfg.quality.preset} samples=${cfg.quality.samples} total=${total} render=${list.length} hdr=${info.hdr}`);
  const t0 = Date.now(); let done = 0; const budget = parseFloat(arg('budget', '0')) * 1000; let cut = false;
  for (const f of list) {
    if (budget && Date.now() - t0 > budget) { cut = true; break; }
    const file = path.join(out, `f_${String(f).padStart(5, '0')}.png`);
    if (fs.existsSync(file)) continue;
    const url = await page.evaluate(t => window.renderFrame(t), f / cfg.fps);
    fs.writeFileSync(file + '.tmp', Buffer.from(url.split(',')[1], 'base64')); fs.renameSync(file + '.tmp', file);
    done++;
    if (done % 5 === 0 || done === 1) console.log(`frame ${f} (${done} done, ${((Date.now() - t0) / 1000 / done).toFixed(2)} s/frame)`);
  }
  console.log(cut ? 'BUDGET（同じコマンドをもう一度実行すれば続きから）' : 'DONE');
  await browser.close();
})();
