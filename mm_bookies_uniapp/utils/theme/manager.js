// Runtime theme support is used by the frontend theme test selector.
import defaultTheme from './defaults.js';
import testPresets from './test-presets.js';

const STORAGE_KEY = 'frontend_theme';
const PRESET_STORAGE_KEY = 'frontend_theme_preset';
const COLOR_PATTERN = /^(#[0-9a-f]{3,8}|rgba?\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}(?:\s*,\s*(?:0|1|0?\.\d+))?\s*\))$/i;
const RADIUS_PATTERN = /^\d+(?:\.\d+)?(?:px|rpx|rem|em|%)$/i;
const URL_PATTERN = /^(https?:\/\/|\/|\.\/|@\/)/i;
const CSS_TOKEN_PATTERN = /^[a-z0-9.%+\/\-\s]+$/i;
const REPEAT_VALUES = new Set(['repeat', 'no-repeat', 'repeat-x', 'repeat-y', 'space', 'round']);

let activeTheme = defaultTheme;

function isColor(value) {
	return typeof value === 'string' && COLOR_PATTERN.test(value.trim());
}

function safeColor(value, fallback) {
	return isColor(value) ? value.trim() : fallback;
}

function safeRadius(value, fallback) {
	return typeof value === 'string' && RADIUS_PATTERN.test(value.trim()) ? value.trim() : fallback;
}

function safeText(value, fallback) {
	if (typeof value !== 'string') {
		return fallback;
	}
	const normalized = value.trim();
	return normalized.length > 0 && normalized.length <= 80 && !/[<>"'\\{};\r\n]/.test(normalized) ?
		normalized :
		fallback;
}

function safeUrl(value) {
	if (typeof value !== 'string' || value.trim().length > 2048 || !URL_PATTERN.test(value.trim())) {
		return '';
	}
	return value.trim().replace(/["'()\\;{}]/g, '');
}

function safeCssTokens(value, fallback, maxTokens) {
	if (typeof value !== 'string') {
		return fallback;
	}
	const normalized = value.trim();
	const tokens = normalized ? normalized.split(/\s+/) : [];
	return normalized.length <= 80 && tokens.length <= maxTokens && CSS_TOKEN_PATTERN.test(normalized) ?
		normalized :
		fallback;
}

function safePosition(value, fallback = 'center') {
	return safeCssTokens(value, fallback, 4);
}

function safeSize(value, fallback = 'cover') {
	return safeCssTokens(value, fallback, 4);
}

function withAlpha(color, alpha) {
	const value = String(color || '').trim();
	const hex = value.match(/^#([0-9a-f]{3,8})$/i);
	if (hex) {
		let digits = hex[1];
		if (digits.length === 3 || digits.length === 4) {
			digits = digits.split('').map((digit) => digit + digit).join('');
		}
		const red = parseInt(digits.slice(0, 2), 16);
		const green = parseInt(digits.slice(2, 4), 16);
		const blue = parseInt(digits.slice(4, 6), 16);
		return `rgba(${red}, ${green}, ${blue}, ${alpha})`;
	}

	const rgb = value.match(/^rgba?\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})/i);
	return rgb ? `rgba(${rgb[1]}, ${rgb[2]}, ${rgb[3]}, ${alpha})` : value;
}

function clamp(value, min, max) {
	const number = Number(value);
	if (!Number.isFinite(number)) {
		return min;
	}
	return Math.min(max, Math.max(min, number));
}

function normalizeStop(stop, fallbackColor) {
	const rawOffset = Number(stop && stop.offset);
	const offset = Number.isFinite(rawOffset) && rawOffset <= 1 ? rawOffset * 100 : rawOffset;
	return {
		offset: clamp(Number.isFinite(offset) ? offset : 0, 0, 100),
		color: safeColor(stop && stop.color, fallbackColor),
	};
}

function renderStops(stops, fallbackColor) {
	return (Array.isArray(stops) ? stops : [])
		.slice(0, 8)
		.map((stop) => normalizeStop(stop, fallbackColor))
		.sort((a, b) => a.offset - b.offset)
		.map((stop) => `${stop.color} ${stop.offset}%`)
		.join(', ');
}

function renderLayer(layer, fallbackColor) {
	if (!layer || !renderStops(layer.stops, fallbackColor)) {
		return '';
	}
	const stops = renderStops(layer.stops, fallbackColor);
	if (layer.type === 'radial') {
		const shape = layer.shape === 'ellipse' ? 'ellipse' : 'circle';
		const position = safePosition(layer.position);
		return `radial-gradient(${shape} at ${position}, ${stops})`;
	}
	const angle = clamp(layer.angle === undefined ? 135 : layer.angle, 0, 360);
	return `linear-gradient(${angle}deg, ${stops})`;
}

function renderBackground(background, fallbackBackground, fallbackImage = '') {
	const source = background && typeof background === 'object' ? background : {};
	const fallbackColor = safeColor(source.fallbackColor, fallbackBackground);
	let image = '';

	if (source.type === 'image') {
		const url = safeUrl(source.url);
		if (url) {
			const overlay = isColor(source.overlay) ? source.overlay : '';
			image = overlay ?
				`linear-gradient(${overlay}, ${overlay}), url("${url}")` :
				`url("${url}")`;
		}
	} else {
		const layers = Array.isArray(source.layers) ? source.layers : [source];
		image = layers
			.map((layer) => renderLayer(layer, fallbackColor))
			.filter(Boolean)
			.join(', ');
	}

	return {
		image: image || fallbackImage,
		color: fallbackColor,
		position: safePosition(source.position),
		placeholderPosition: safePosition(source.placeholderPosition, safePosition(source.position)),
		size: safeSize(source.size),
		repeat: REPEAT_VALUES.has(source.repeat) ? source.repeat : 'no-repeat',
	};
}

function normalizeTheme(theme) {
	const source = theme && typeof theme === 'object' ? theme : {};
	const tokens = source.tokens && typeof source.tokens === 'object' ? source.tokens : {};
	const defaults = defaultTheme.tokens;
	const backgrounds = source.backgrounds && typeof source.backgrounds === 'object' ?
		source.backgrounds :
		{};
	const defaultBackgrounds = defaultTheme.backgrounds;
	const defaultHome = renderBackground(defaultBackgrounds.home, '#1E1B4B');
	const defaultAuth = renderBackground(defaultBackgrounds.auth, '#1E1B4B');
	const defaultHeader = renderBackground(defaultBackgrounds.header, '#1E1B4B');
	const defaultPage = renderBackground(defaultBackgrounds.page, '#1E1B4B');
	const defaultNoHeader = renderBackground(defaultBackgrounds.noHeader || defaultBackgrounds.home, '#1E1B4B',
		defaultHome.image);
	const defaultWithHeader = renderBackground(defaultBackgrounds.withHeader || defaultBackgrounds.page, '#1E1B4B',
		defaultPage.image);
	const defaultLogin = renderBackground(defaultBackgrounds.login || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image);
	const defaultRegister = renderBackground(defaultBackgrounds.register || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image);
	const primary = safeColor(tokens.primary, defaults.primary);
	const secondary = safeColor(tokens.secondary, defaults.secondary);
	const rawNoHeader = backgrounds.noHeader || backgrounds.home || backgrounds.auth ||
		defaultBackgrounds.noHeader || defaultBackgrounds.home;
	const rawWithHeader = backgrounds.withHeader || backgrounds.page ||
		defaultBackgrounds.withHeader || defaultBackgrounds.page;
	const rawHeader = backgrounds.header || defaultBackgrounds.header;
	const isImageBackground = (background) => background && (background.type === 'image' || background.url);
	const sharedGradient = !isImageBackground(rawNoHeader) &&
		!isImageBackground(rawWithHeader) &&
		!isImageBackground(rawHeader);

	const normalizedBackgrounds = {
		noHeader: renderBackground(rawNoHeader, '#1E1B4B', defaultNoHeader.image),
		withHeader: renderBackground(rawWithHeader, '#1E1B4B', defaultWithHeader.image),
		home: renderBackground(backgrounds.home || defaultBackgrounds.home, '#1E1B4B', defaultHome.image),
		auth: renderBackground(backgrounds.auth || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image),
		login: renderBackground(backgrounds.login || backgrounds.auth || defaultBackgrounds.login || defaultBackgrounds.auth,
			'#1E1B4B', defaultLogin.image),
		register: renderBackground(backgrounds.register || backgrounds.auth || defaultBackgrounds.register ||
			defaultBackgrounds.auth, '#1E1B4B', defaultRegister.image),
		header: renderBackground(rawHeader, '#1E1B4B', defaultHeader.image),
		page: renderBackground(backgrounds.page || defaultBackgrounds.page, '#1E1B4B', defaultPage.image),
	};

	return {
		version: source.version || defaultTheme.version,
		preset: source.preset || '',
		sharedGradient,
		tokens: {
			title: safeText(tokens.title, defaults.title || 'MM Bookies'),
			subtitle: safeText(tokens.subtitle, defaults.subtitle || ''),
			primary,
			border: safeColor(tokens.border, primary),
			borderOther: safeColor(tokens.borderOther, defaults.borderOther || primary),
			secondary,
			secondaryLight: safeColor(tokens.secondaryLight, defaults.secondaryLight),
			active: safeColor(tokens.active, defaults.active),
			textPrimary: safeColor(tokens.textPrimary, defaults.textPrimary),
			textSecondary: safeColor(tokens.textSecondary, defaults.textSecondary),
			backgroundLight: safeColor(tokens.backgroundLight, defaults.backgroundLight || secondary),
			backgroundInfo: safeColor(tokens.backgroundInfo, defaults.backgroundInfo || '#E8F4F5'),
			bgLoginInput: safeColor(tokens.bgLoginInput, defaults.bgLoginInput || 'rgba(105, 145, 149, 0.6)'),
			colorLoginInput: safeColor(tokens.colorLoginInput, defaults.colorLoginInput || '#FFFFFF'),
			iconPrimary: safeColor(tokens.iconPrimary, primary),
			iconSecondary: safeColor(tokens.iconSecondary, secondary),
			iconOnPrimary: safeColor(tokens.iconOnPrimary, defaults.iconOnPrimary),
			surface: safeColor(tokens.surface, defaults.surface),
			radiusLarge: safeRadius(tokens.radiusLarge, defaults.radiusLarge),
			radiusMedium: safeRadius(tokens.radiusMedium, defaults.radiusMedium),
			radiusSmall: safeRadius(tokens.radiusSmall, defaults.radiusSmall),
			background: tokens.background === 'light' ? 'light' : 'dark',
			headerBackground: tokens.headerBackground === 'light' ? 'light' : 'dark',
			headerLogoBg: tokens.headerLogoBg === 'white' ? 'white' : 'none',
			headerLogoRadius: safeRadius(tokens.headerLogoRadius,
				tokens.headerLogoBg === 'white' ? safeRadius(tokens.radiusLarge, '0') : '0'),
			homeTopBorder: safeColor(tokens.homeTopBorder, primary),
			logoImage: safeUrl(tokens.logoImage),
		},
		backgrounds: normalizedBackgrounds,
	};
}

function getRootElement() {
	if (typeof document !== 'undefined' && document.documentElement) {
		return document.documentElement;
	}
	return null;
}

function getRootStyle() {
	const root = getRootElement();
	return root ? root.style : null;
}

function quoteCssText(value) {
	return `"${String(value || '').replace(/\\/g, '\\\\').replace(/"/g, '\\"')}"`;
}

function applyCssVariables(theme) {
	const rootStyle = getRootStyle();
	if (!rootStyle) {
		return;
	}

	const tokens = theme.tokens;
	const backgroundForeground = tokens.background === 'light' ?
		tokens.primary :
		'#FFFFFF';
	const backgroundForegroundFilter = tokens.background === 'light' ?
		'brightness(0) saturate(100%) invert(71%) sepia(95%) saturate(250%) hue-rotate(77deg) brightness(42%) contrast(169%)' :
		'brightness(0) invert(1)';
	const headerForeground = tokens.headerBackground === 'light' ?
		tokens.primary :
		'#FFFFFF';
	const headerForegroundFilter = tokens.headerBackground === 'light' ?
		'brightness(0) saturate(100%) invert(71%) sepia(95%) saturate(250%) hue-rotate(77deg) brightness(42%) contrast(169%)' :
		'brightness(0) invert(1)';
	const variables = {
		'--theme-primary': tokens.primary,
		'--theme-title': quoteCssText(tokens.title),
		'--theme-subtitle': quoteCssText(tokens.subtitle),
		'--theme-border': tokens.border,
		'--theme-border-other': tokens.borderOther,
		'--theme-secondary': tokens.secondary,
		'--theme-secondary-light': tokens.secondaryLight,
		'--theme-active': tokens.active,
		'--theme-text-primary': tokens.textPrimary,
		'--theme-text-secondary': tokens.textSecondary,
		'--theme-bg-light': tokens.backgroundLight,
		'--theme-bg-info': tokens.backgroundInfo,
		'--theme-bg-login-input': tokens.bgLoginInput,
		'--theme-color-login-input': tokens.colorLoginInput,
		'--theme-icon-primary': tokens.iconPrimary,
		'--theme-icon-secondary': tokens.iconSecondary,
		'--theme-icon-on-primary': tokens.iconOnPrimary,
		'--theme-surface': tokens.surface,
		'--theme-radius-large': tokens.radiusLarge,
		'--theme-radius-medium': tokens.radiusMedium,
		'--theme-radius-small': tokens.radiusSmall,
		'--theme-primary-alpha-06': withAlpha(tokens.primary, 0.06),
		'--theme-primary-alpha-18': withAlpha(tokens.primary, 0.18),
		'--theme-primary-alpha-20': withAlpha(tokens.primary, 0.2),
		'--theme-secondary-alpha-20': withAlpha(tokens.secondary, 0.2),
		'--theme-background': tokens.background,
		'--theme-header-background': tokens.headerBackground,
		'--theme-header-logo-bg': tokens.headerLogoBg,
		'--theme-header-logo-padding': tokens.headerLogoBg === 'white' ? '0 12px' : '0',
		'--theme-header-logo-radius': tokens.headerLogoRadius,
		'--theme-home-top-border': tokens.homeTopBorder,
		'--theme-logo-image': tokens.logoImage ? `url("${tokens.logoImage}")` : 'none',
		'--theme-background-foreground': backgroundForeground,
		'--theme-background-foreground-filter': backgroundForegroundFilter,
		'--theme-header-background-foreground': headerForeground,
		'--theme-header-background-foreground-filter': headerForegroundFilter,
		'--theme-auth-button-background': tokens.background === 'light' ? tokens.primary : '#FFFFFF',
		'--theme-auth-button-foreground': tokens.background === 'light' ? '#FFFFFF' : tokens.primary,
	};

	const setBackgroundVariables = (name, background) => {
		const cssName = {
			noHeader: 'no-header',
			withHeader: 'with-header',
		}[name] || name;
		variables[`--theme-${cssName}-background-image`] = background.image;
		variables[`--theme-${cssName}-background-color`] = background.color;
		variables[`--theme-${cssName}-background-position`] = background.position;
		variables[`--theme-${cssName}-background-size`] = background.size;
		variables[`--theme-${cssName}-background-repeat`] = background.repeat;
	};

	Object.keys(theme.backgrounds).forEach((name) => {
		setBackgroundVariables(name, theme.backgrounds[name]);
	});

	const transparentBackground = {
		image: 'none',
		color: 'transparent',
		position: 'center',
		size: 'cover',
		repeat: 'no-repeat',
	};
	setBackgroundVariables('app', theme.sharedGradient ? theme.backgrounds.home : theme.backgrounds.withHeader);
	setBackgroundVariables('header', theme.sharedGradient ? transparentBackground : theme.backgrounds.header);
	setBackgroundVariables('withHeader', theme.sharedGradient ? transparentBackground : theme.backgrounds.withHeader);
	variables['--theme-header-placeholder-position'] = theme.backgrounds.header.placeholderPosition;

	Object.keys(variables).forEach((name) => {
		rootStyle.setProperty(name, variables[name]);
	});

	const root = getRootElement();
	if (root) {
		root.setAttribute('data-theme-preset', theme.preset || '');
	}
}

function emitThemeUpdated(theme) {
	if (typeof uni !== 'undefined' && typeof uni.$emit === 'function') {
		uni.$emit('theme:updated', theme);
	}
}

function apply(theme, options = {}) {
	const normalized = normalizeTheme(theme);
	activeTheme = normalized;
	applyCssVariables(normalized);

	if (options.persist !== false && typeof uni !== 'undefined') {
		uni.setStorageSync(STORAGE_KEY, normalized);
	}

	emitThemeUpdated(normalized);
	return normalized;
}

function applyPreset(name, options = {}) {
	const preset = testPresets[name];
	if (!preset) {
		throw new Error(`Unknown theme preset: ${name}`);
	}

	if (options.persist !== false && typeof uni !== 'undefined') {
		uni.setStorageSync(PRESET_STORAGE_KEY, name);
	}

	return apply(preset, options);
}

function initPreset() {
	if (typeof uni === 'undefined') {
		return activeTheme;
	}

	const preset = uni.getStorageSync(PRESET_STORAGE_KEY);
	return preset && testPresets[preset] ?
		applyPreset(preset, {
			persist: false,
		}) :
		activeTheme;
}

function readCachedTheme() {
	if (typeof uni === 'undefined') {
		return null;
	}
	const cached = uni.getStorageSync(STORAGE_KEY);
	return cached && typeof cached === 'object' ? cached : null;
}

function parseObject(value) {
	if (value && typeof value === 'object' && !Array.isArray(value)) {
		return value;
	}
	if (typeof value !== 'string') {
		return null;
	}
	try {
		const parsed = JSON.parse(value);
		return parsed && typeof parsed === 'object' && !Array.isArray(parsed) ? parsed : null;
	} catch (error) {
		return null;
	}
}

function coerceTheme(value) {
	const source = parseObject(value);
	if (!source) {
		return null;
	}

	const tokens = parseObject(source.tokens) || {};
	const backgrounds = parseObject(source.backgrounds) || {};
	const hasToken = ['title', 'themeTitle', 'theme_title', 'primary', 'secondary', 'border', 'borderOther', 'borderOtherColor', 'bgLoginInput',
		'backgroundLoginInput', 'colorLoginInput', 'loginInputColor', 'primaryColor', 'secondaryColor',
		'borderColor', 'border_other', 'border_other_color', 'bg_login_input', 'background_login_input',
		'color_login_input', 'login_input_color', 'primary_color', 'secondary_color', 'border_color'].some((name) =>
		source[name] !== undefined || tokens[name] !== undefined);
	const hasBackground = Object.keys(backgrounds).length > 0 ||
		['noHeader', 'withHeader', 'home', 'login', 'register', 'header', 'page', 'noHeaderBackground',
			'withHeaderBackground', 'homeBackground', 'headerBackground'].some((name) =>
			source[name] !== undefined);

	if (!hasToken && !hasBackground) {
		return null;
	}

	const tokenAliases = {
		title: ['title', 'themeTitle', 'theme_title'],
		primary: ['primary', 'primaryColor', 'primary_color'],
		border: ['border', 'borderColor', 'border_color'],
		borderOther: ['borderOther', 'border_other', 'borderOtherColor', 'border_other_color'],
		secondary: ['secondary', 'secondaryColor', 'secondary_color'],
		secondaryLight: ['secondaryLight', 'secondary_light'],
		active: ['active', 'activeColor', 'active_color'],
		textPrimary: ['textPrimary', 'text_primary'],
		textSecondary: ['textSecondary', 'text_secondary'],
		backgroundLight: ['backgroundLight', 'background_light'],
		bgLoginInput: ['bgLoginInput', 'bg_login_input', 'backgroundLoginInput', 'background_login_input'],
		colorLoginInput: ['colorLoginInput', 'color_login_input', 'loginInputColor', 'login_input_color'],
		iconPrimary: ['iconPrimary', 'icon_primary'],
		iconSecondary: ['iconSecondary', 'icon_secondary'],
		iconOnPrimary: ['iconOnPrimary', 'icon_on_primary'],
		surface: ['surface'],
	};
	const normalizedTokens = { ...tokens };
	Object.keys(tokenAliases).forEach((name) => {
		if (normalizedTokens[name] !== undefined) {
			return;
		}
		const alias = tokenAliases[name].find((key) =>
			source[key] !== undefined || tokens[key] !== undefined);
		if (alias) {
			normalizedTokens[name] = source[alias] !== undefined ? source[alias] : tokens[alias];
		}
	});

	const normalizedBackgrounds = { ...backgrounds };
	['noHeader', 'withHeader', 'home', 'login', 'register', 'header', 'page'].forEach((name) => {
		if (normalizedBackgrounds[name] !== undefined) {
			normalizedBackgrounds[name] = parseObject(normalizedBackgrounds[name]) || normalizedBackgrounds[name];
			return;
		}
		const value = source[`${name}Background`] || source[name];
		normalizedBackgrounds[name] = parseObject(value) || value;
	});

	return {
		version: source.version,
		tokens: normalizedTokens,
		backgrounds: normalizedBackgrounds,
	};
}

function extractTheme(config) {
	const source = parseObject(config);
	if (!source) {
		return null;
	}

	const nestedData = parseObject(source.data);
	const nestedItems = parseObject(source.items);
	const candidates = [
		source.theme,
		source.front_theme,
		source.frontTheme,
		source.front_theme_config,
		source.frontThemeConfig,
		nestedData && (nestedData.theme || nestedData.front_theme || nestedData.frontTheme),
		nestedItems && (nestedItems.theme || nestedItems.front_theme || nestedItems.frontTheme),
		source,
		nestedData,
		nestedItems,
	];

	for (const candidate of candidates) {
		const theme = coerceTheme(candidate);
		if (theme) {
			return theme;
		}
	}
	return null;
}

function init() {
	const cached = readCachedTheme();
	return apply(cached || defaultTheme, {
		persist: false,
	});
}

function applyFromConfig(config) {
	const theme = extractTheme(config);
	return theme ? apply(theme) : activeTheme;
}

function getBackgroundStyle(name) {
	const background = activeTheme.backgrounds && activeTheme.backgrounds[name];
	if (!background) {
		return {};
	}
	return {
		backgroundColor: background.color,
		backgroundImage: background.image || 'none',
		backgroundPosition: background.position,
		backgroundSize: background.size,
		backgroundRepeat: background.repeat,
	};
}

function load(url) {
	if (!url || typeof uni === 'undefined') {
		return Promise.resolve(null);
	}

	return new Promise((resolve, reject) => {
		uni.request({
			url,
			method: 'GET',
			success: (response) => {
				if (response.statusCode < 200 || response.statusCode >= 300) {
					reject(new Error(`Theme request failed: ${response.statusCode}`));
					return;
				}
				const payload = response.data && (response.data.data || response.data);
				const theme = extractTheme(payload);
				if (!theme) {
					reject(new Error('Theme response does not contain a valid theme'));
					return;
				}
				resolve(apply(theme));
			},
			fail: reject,
		});
	});
}

export default {
	init,
	initPreset,
	apply,
	applyPreset,
	applyFromConfig,
	getBackgroundStyle,
	load,
	get current() {
		return activeTheme;
	},
};
