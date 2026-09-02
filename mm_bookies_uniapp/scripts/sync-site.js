/**
 * 站点统一同步脚本
 * 唯一来源：siteinfo.js 中的 site 字段。
 * 运行后自动把站点同步到：
 *   - uni.scss          -> $site（主题色）
 *   - manifest.json     -> name（App 桌面名）
 *   - pages.json        -> globalStyle.navigationBarTitleText（H5 页签标题）
 *
 * 用法：node scripts/sync-site.js
 * （每次切换站点：改 siteinfo.js 的 site 后，跑一次本脚本再打包）
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname, '..');

// 站点 -> 显示名（与 siteinfo.js 中的 site 键保持一致）
const TITLES = {
	mmbookies: 'MM Bookies',
	shwegoal: 'Shwe Goal',
	phoe_wa_maung: 'Phoe Wa Maung',
};

// 从 siteinfo.js 读取激活的站点（跳过 // 注释行，取最后一个生效的 site）
function readActiveSite() {
	const src = fs.readFileSync(path.join(ROOT, 'siteinfo.js'), 'utf8');
	const lines = src.split(/\r?\n/);
	for (let i = lines.length - 1; i >= 0; i--) {
		const line = lines[i];
		if (line.includes('//')) continue;
		const m = line.match(/^\s*"site"\s*:\s*"([^"]+)"/);
		if (m) return m[1];
	}
	throw new Error('siteinfo.js 中未找到生效的 site 字段');
}

// 就地正则替换，保留文件其余内容（含注释）
function patchFile(file, re, to) {
	const f = path.join(ROOT, file);
	const src = fs.readFileSync(f, 'utf8');
	if (!re.test(src)) throw new Error(file + ' 未匹配到可替换项');
	fs.writeFileSync(f, src.replace(re, to), 'utf8');
	console.log('已同步 ' + file);
}

const site = readActiveSite();
const title = TITLES[site];
if (!title) throw new Error('未知站点: ' + site + '（请在 sync-site.js 的 TITLES 中补充）');

console.log('当前站点: ' + site + ' → ' + title);

// 1. uni.scss: $site: phoe_wa_maung;
patchFile('uni.scss', /(\$site\s*:\s*)[^;\n]+;/, '$1' + site + ';');

// 2. manifest.json: "name": "Phoe Wa Maung"
patchFile('manifest.json', /("name"\s*:\s*")[^"]*"/, '$1' + title + '"');

// 3. pages.json: globalStyle 内的 navigationBarTitleText
patchFile(
	'pages.json',
	/("globalStyle"[\s\S]*?\n[ \t]*"navigationBarTitleText"[ \t]*:[ \t]*")[^"]*"/,
	'$1' + title + '"'
);

console.log('同步完成，请重新编译。');