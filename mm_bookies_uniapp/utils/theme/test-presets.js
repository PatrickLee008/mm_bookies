const mmBookiesGradient = {
	type: 'gradient',
	layers: [{
		type: 'radial',
		shape: 'circle',
		position: '0% 100%',
		stops: [{
			offset: 0,
			color: '#36BCCB',
		}, {
			offset: 30,
			color: '#103D43',
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
			color: '#36BCCB',
		}, {
			offset: 30,
			color: '#103D43',
		}, {
			offset: 50,
			color: 'rgba(255, 255, 255, 0)',
		}],
	}, {
		type: 'linear',
		angle: 135,
		stops: [{
			offset: 0,
			color: '#103D43',
		}, {
			offset: 56,
			color: '#103D43',
		}, {
			offset: 100,
			color: '#103D43',
		}],
	}],
	fallbackColor: '#103D43',
	position: 'center',
	size: 'cover',
	repeat: 'no-repeat',
};

function imageBackground(url, fallbackColor, options = {}) {
	return {
		type: 'image',
		url,
		fallbackColor,
		position: options.position || 'center',
		size: options.size || 'cover',
		repeat: options.repeat || 'no-repeat',
	};
}

const mmBookies = {
	version: 'test-mm-bookies',
	preset: 'mm-bookies',
	tokens: {
		title: 'MM Bookies',
		subtitle: 'ရွှေမြန်မာတို့ အကြိုက် မြန်မာဘောဒိုင်',
		primary: '#1C667C',
		border: '#2A626833',
		borderOther: 'rgba(0, 0, 0, 0)',
		secondary: '#37BDCC',
		secondaryLight: '#F1FAFB',
		active: '#FFC857',
		textPrimary: '#1C667C',
		textSecondary: '#1C667C',
		backgroundLight: '#17A2B8',
		backgroundInfo: '#E8F4F5',
		bgLoginInput: 'rgba(105, 145, 149, 0.6)',
		colorLoginInput: '#FFFFFF',
		iconPrimary: '#1C667C',
		iconSecondary: '#37BDCC',
		iconOnPrimary: '#FFFFFF',
		surface: '#FFFFFF',
		radiusLarge: '16px',
		radiusMedium: '12px',
		radiusSmall: '8px',
		background: 'dark',
		headerBackground: 'dark',
		headerLogoBg: 'none',
		headerLogoRadius: '0',
		homeTopBorder: '#44696E',
		logoImage: '/static/theme/mm-bookies/mm-bookies_logo.png',
	},
	backgrounds: {
		home: mmBookiesGradient,
		auth: mmBookiesGradient,
		login: mmBookiesGradient,
		register: mmBookiesGradient,
		noHeader: mmBookiesGradient,
		withHeader: mmBookiesGradient,
		header: mmBookiesGradient,
		page: mmBookiesGradient,
	},
};

const shweGoalBackground = imageBackground('/static/theme/bg-green.png', '#136201');
const shweGoalHeaderBackground = imageBackground('/static/theme/bg-green.png', '#136201', {
	position: 'center top',
	size: '100% 552px',
});

const shweGoal = {
	version: 'test-shwe-goal',
	preset: 'shwe-goal',
	tokens: {
		title: 'Shwe Goal',
		subtitle: 'အနိုင်ရဖို့ ရွှေဂိုးတစ်ဂိုးသာလိုပါတယ်',
		primary: '#136201',
		border: '#136201',
		borderOther: '#A0FF82',
		secondary: '#3C9320',
		secondaryLight: '#81BB1D',
		active: '#89D423',
		textPrimary: '#136201',
		textSecondary: '#3C9320',
		backgroundLight: '#17A2B8',
		backgroundInfo: '#EDEDED',
		bgLoginInput: 'rgba(0, 0, 0, 0.3)',
		colorLoginInput: '#FFFFFF',
		iconPrimary: '#136201',
		iconSecondary: '#3C9320',
		iconOnPrimary: '#FFFFFF',
		surface: '#FFFFFF',
		radiusLarge: '8px',
		radiusMedium: '8px',
		radiusSmall: '4px',
		background: 'dark',
		headerBackground: 'dark',
		headerLogoBg: 'none',
		headerLogoRadius: '0',
		homeTopBorder: '#A0FF82',
		logoImage: '/static/theme/test/shwegoal_logo.png',
	},
	backgrounds: {
		home: shweGoalBackground,
		auth: shweGoalBackground,
		login: shweGoalBackground,
		register: shweGoalBackground,
		noHeader: shweGoalBackground,
		withHeader: shweGoalBackground,
		header: shweGoalHeaderBackground,
		page: shweGoalBackground,
	},
};

const phoeWaMaungWithHeaderBackground = imageBackground('/static/theme/bg-green.png', '#136201');
const phoeWaMaungHeaderBackground = imageBackground('/static/theme/bg-green.png', '#136201', {
	position: 'center top',
	size: '100% 552px',
});

const phoeWaMaung = {
	version: 'test-phoe-wa-maung',
	preset: 'phoe-wa-maung',
	tokens: {
		title: 'Phoe Wa Maung',
		subtitle: 'ငွေကြေးခိုင်မာ ယုံကြည်စိတ်ချ ညီကိုတိုအားလုံးအတွက် ဖိုးဝ',
		primary: '#005E12',
		border: '#136201',
		borderOther: '#99BA4A',
		secondary: '#3C9320',
		secondaryLight: '#81BB1D',
		active: '#89D423',
		textPrimary: '#136201',
		textSecondary: '#3C9320',
		backgroundLight: '#17A2B8',
		backgroundInfo: '#F2F2F2',
		bgLoginInput: '#FFFFFF',
		colorLoginInput: '#005E12',
		iconPrimary: '#005E12',
		iconSecondary: '#3C9320',
		iconOnPrimary: '#FFFFFF',
		surface: '#FFFFFF',
		radiusLarge: '12px',
		radiusMedium: '8px',
		radiusSmall: '4px',
		background: 'light',
		headerBackground: 'dark',
		headerLogoBg: 'white',
		headerLogoRadius: '12px',
		homeTopBorder: '#028206',
		logoImage: '/static/theme/test-old/phoewaa_maung_logo.png',
	},
	backgrounds: {
		home: imageBackground('/static/theme/bg-white.png', '#136201'),
		auth: imageBackground('/static/theme/bg-white.png', '#136201'),
		login: imageBackground('/static/theme/bg-white.png', '#136201'),
		register: imageBackground('/static/theme/bg-white.png', '#136201'),
		noHeader: imageBackground('/static/theme/bg-white.png', '#136201'),
		withHeader: phoeWaMaungWithHeaderBackground,
		header: phoeWaMaungHeaderBackground,
		page: phoeWaMaungWithHeaderBackground,
	},
};

export default {
	'mm-bookies': mmBookies,
	'shwe-goal': shweGoal,
	'phoe-wa-maung': phoeWaMaung,
};
