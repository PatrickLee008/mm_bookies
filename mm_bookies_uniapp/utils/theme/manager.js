// Runtime theme support is kept for a later phase and is not initialized in
// the current frontend-only color debugging mode.
import defaultTheme from './defaults.js';

const STORAGE_KEY = 'frontend_theme';
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
	const defaultHeader = renderBackground(defaultBackgrounds.header, '#312E81');
	const defaultPage = renderBackground(defaultBackgrounds.page, '#312E81');
	const defaultNoHeader = renderBackground(defaultBackgrounds.noHeader || defaultBackgrounds.home, '#1E1B4B',
		defaultHome.image);
	const defaultWithHeader = renderBackground(defaultBackgrounds.withHeader || defaultBackgrounds.page, '#312E81',
		defaultPage.image);
	const defaultLogin = renderBackground(defaultBackgrounds.login || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image);
	const defaultRegister = renderBackground(defaultBackgrounds.register || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image);
	const primary = safeColor(tokens.primary, defaults.primary);
	const secondary = safeColor(tokens.secondary, defaults.secondary);

	return {
		version: source.version || defaultTheme.version,
		tokens: {
			primary,
			secondary,
			secondaryLight: safeColor(tokens.secondaryLight, defaults.secondaryLight),
			active: safeColor(tokens.active, defaults.active),
			textPrimary: safeColor(tokens.textPrimary, defaults.textPrimary),
			textSecondary: safeColor(tokens.textSecondary, defaults.textSecondary),
			backgroundLight: safeColor(tokens.backgroundLight, defaults.backgroundLight || secondary),
			backgroundInfo: safeColor(tokens.backgroundInfo, defaults.backgroundInfo || '#E8F4F5'),
			iconPrimary: safeColor(tokens.iconPrimary, primary),
			iconSecondary: safeColor(tokens.iconSecondary, secondary),
			iconOnPrimary: safeColor(tokens.iconOnPrimary, defaults.iconOnPrimary),
			surface: safeColor(tokens.surface, defaults.surface),
			radiusLarge: safeRadius(tokens.radiusLarge, defaults.radiusLarge),
			radiusMedium: safeRadius(tokens.radiusMedium, defaults.radiusMedium),
			radiusSmall: safeRadius(tokens.radiusSmall, defaults.radiusSmall),
		},
		backgrounds: {
			noHeader: renderBackground(backgrounds.noHeader || backgrounds.home || backgrounds.auth ||
				defaultBackgrounds.noHeader || defaultBackgrounds.home, '#1E1B4B', defaultNoHeader.image),
			withHeader: renderBackground(backgrounds.withHeader || backgrounds.page ||
				defaultBackgrounds.withHeader || defaultBackgrounds.page, '#312E81', defaultWithHeader.image),
			home: renderBackground(backgrounds.home || defaultBackgrounds.home, '#1E1B4B', defaultHome.image),
			auth: renderBackground(backgrounds.auth || defaultBackgrounds.auth, '#1E1B4B', defaultAuth.image),
			login: renderBackground(backgrounds.login || backgrounds.auth || defaultBackgrounds.login || defaultBackgrounds.auth,
				'#1E1B4B', defaultLogin.image),
			register: renderBackground(backgrounds.register || backgrounds.auth || defaultBackgrounds.register ||
				defaultBackgrounds.auth, '#1E1B4B', defaultRegister.image),
			header: renderBackground(backgrounds.header || defaultBackgrounds.header, '#312E81', defaultHeader.image),
			page: renderBackground(backgrounds.page || defaultBackgrounds.page, '#312E81', defaultPage.image),
		},
	};
}

function getRootStyle() {
	if (typeof document !== 'undefined' && document.documentElement) {
		return document.documentElement.style;
	}
	return null;
}

function applyCssVariables(theme) {
	const rootStyle = getRootStyle();
	if (!rootStyle) {
		return;
	}

	const tokens = theme.tokens;
	const variables = {
		'--theme-primary': tokens.primary,
		'--theme-secondary': tokens.secondary,
		'--theme-secondary-light': tokens.secondaryLight,
		'--theme-active': tokens.active,
		'--theme-text-primary': tokens.textPrimary,
		'--theme-text-secondary': tokens.textSecondary,
		'--theme-bg-light': tokens.backgroundLight,
		'--theme-bg-info': tokens.backgroundInfo,
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
	};

	Object.keys(theme.backgrounds).forEach((name) => {
		const background = theme.backgrounds[name];
		variables[`--theme-${name}-background-image`] = background.image;
		variables[`--theme-${name}-background-color`] = background.color;
		variables[`--theme-${name}-background-position`] = background.position;
		variables[`--theme-${name}-background-size`] = background.size;
		variables[`--theme-${name}-background-repeat`] = background.repeat;
	});
	variables['--theme-header-placeholder-position'] = theme.backgrounds.header.placeholderPosition;

	Object.keys(variables).forEach((name) => {
		rootStyle.setProperty(name, variables[name]);
	});
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
	const hasToken = ['primary', 'secondary', 'primaryColor', 'secondaryColor', 'primary_color',
		'secondary_color'].some((name) => source[name] !== undefined || tokens[name] !== undefined);
	const hasBackground = Object.keys(backgrounds).length > 0 ||
		['noHeader', 'withHeader', 'home', 'login', 'register', 'header', 'page', 'noHeaderBackground',
			'withHeaderBackground', 'homeBackground', 'headerBackground'].some((name) =>
			source[name] !== undefined);

	if (!hasToken && !hasBackground) {
		return null;
	}

	const tokenAliases = {
		primary: ['primary', 'primaryColor', 'primary_color'],
		secondary: ['secondary', 'secondaryColor', 'secondary_color'],
		secondaryLight: ['secondaryLight', 'secondary_light'],
		active: ['active', 'activeColor', 'active_color'],
		textPrimary: ['textPrimary', 'text_primary'],
		textSecondary: ['textSecondary', 'text_secondary'],
		backgroundLight: ['backgroundLight', 'background_light'],
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
		const alias = tokenAliases[name].find((key) => source[key] !== undefined);
		if (alias) {
			normalizedTokens[name] = source[alias];
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
	apply,
	applyFromConfig,
	getBackgroundStyle,
	load,
	get current() {
		return activeTheme;
	},
};
