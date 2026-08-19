// Reserved for the future runtime theme flow. Static debugging currently uses
// uni.scss and common/styles/_theme-presets.scss.
const testTheme = {
	version: 'test',
	tokens: {
		title: 'MM Bookies',
		headerLogoType: 'text',
		primary: '#6D28D9',
		border: '#6D28D9',
		borderOther: '#A5B4FC',
		secondary: '#06B6D4',
		secondaryLight: '#ECFEFF',
		active: '#F59E0B',
		textPrimary: '#4C1D95',
		textSecondary: '#475569',
		backgroundLight: '#0891B2',
		backgroundInfo: '#E8F4F5',
		bgLoginInput: 'rgba(105, 145, 149, 0.6)',
		colorLoginInput: '#FFFFFF',
		iconPrimary: '#6D28D9',
		iconSecondary: '#06B6D4',
		iconOnPrimary: '#FFFFFF',
		surface: '#FFFFFF',
		radiusLarge: '12px',
		radiusMedium: '8px',
		radiusSmall: '4px',
	},
	backgrounds: {
		home: {
			type: 'gradient',
			layers: [{
				type: 'radial',
				shape: 'circle',
				position: '0% 100%',
				stops: [{
					offset: 0,
					color: '#22D3EE',
				}, {
					offset: 30,
					color: '#1E1B4B',
				}, {
					offset: 50,
					color: 'rgba(255, 255, 255, 0)',
				}],
			}, {
				type: 'radial',
				shape: 'circle',
				position: '100% 0%',
				stops: [{
					offset: 0,
					color: '#22D3EE',
				}, {
					offset: 30,
					color: '#1E1B4B',
				}, {
					offset: 50,
					color: 'rgba(255, 255, 255, 0)',
				}],
			}, {
				type: 'linear',
				angle: 135,
				stops: [{
					offset: 0,
					color: '#1E1B4B',
				}, {
					offset: 56,
					color: '#1E1B4B',
				}, {
					offset: 100,
					color: '#0F766E',
				}],
			}],
			fallbackColor: '#1E1B4B',
			position: 'center',
			size: 'cover',
			repeat: 'no-repeat',
		},
		auth: {
			type: 'gradient',
			angle: 135,
			stops: [{
				offset: 0,
				color: '#1E1B4B',
			}, {
				offset: 100,
				color: '#0F766E',
			}],
			fallbackColor: '#1E1B4B',
			position: 'center',
			size: 'cover',
			repeat: 'no-repeat',
		},
		header: {
			type: 'gradient',
			layers: [{
				type: 'radial',
				shape: 'circle',
				position: '100% 0%',
				stops: [{
					offset: 0,
					color: '#22D3EE',
				}, {
					offset: 34,
					color: '#0891B2',
				}, {
					offset: 68,
					color: 'rgba(255, 255, 255, 0)',
				}],
			}, {
				type: 'linear',
				angle: 135,
				stops: [{
					offset: 0,
					color: '#1E1B4B',
				}, {
					offset: 56,
					color: '#1E1B4B',
				}, {
					offset: 100,
					color: '#0891B2',
				}],
			}],
			fallbackColor: '#1E1B4B',
			position: 'center top',
			placeholderPosition: 'center -255px',
			size: '100% 552px',
			repeat: 'no-repeat',
		},
		page: {
			type: 'gradient',
			angle: 135,
			stops: [{
				offset: 0,
				color: '#1E1B4B',
			}, {
				offset: 100,
				color: '#0891B2',
			}],
			fallbackColor: '#1E1B4B',
			position: 'center',
			size: 'cover',
			repeat: 'no-repeat',
		},
	},
};

// Use the home background as the single fallback for every gradient page group.
const homeBackground = testTheme.backgrounds.home;
testTheme.backgrounds.auth = homeBackground;
testTheme.backgrounds.login = homeBackground;
testTheme.backgrounds.register = homeBackground;
testTheme.backgrounds.header = {
	...homeBackground,
	placeholderPosition: 'center -255px',
	size: '100% 552px',
};
testTheme.backgrounds.page = homeBackground;
testTheme.backgrounds.noHeader = homeBackground;
testTheme.backgrounds.withHeader = homeBackground;

export default testTheme;
