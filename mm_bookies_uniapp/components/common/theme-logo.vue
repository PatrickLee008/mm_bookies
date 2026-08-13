<template>
	<view class="theme-logo" :class="`theme-logo-${variant}`" :style="{ height: cssHeight }">
		<image class="theme-logo-image theme-logo-image-legacy"
			src="/static/theme/legacy/mm_bookies_logo.png" mode="heightFix"
			:style="{ height: cssHeight }"></image>
		<image class="theme-logo-image theme-logo-image-shwe-goal"
			src="/static/theme/test/shwegoal_logo.png" mode="heightFix"
			:style="{ height: cssHeight }"></image>
		<image class="theme-logo-image theme-logo-image-phoe-wa-maung"
			src="/static/theme/test-old/phoewaa_maung_logo.png" mode="heightFix"
			:style="{ height: cssHeight }"></image>
	</view>
</template>

<script>
	export default {
		name: 'ThemeLogo',
		props: {
			variant: {
				type: String,
				default: 'header',
			},
			height: {
				type: [String, Number],
				default: '32px',
			},
		},
		computed: {
			cssHeight() {
				return typeof this.height === 'number' ? `${this.height}px` : this.height
			},
		},
	}
</script>

<style lang="scss" scoped>
	.theme-logo {
		display: inline-flex;
		align-items: center;
		justify-content: center;
		width: auto;
		flex-shrink: 0;
		overflow: visible;
	}

	.theme-logo-header {
		background: var(--theme-header-logo-bg, none);
		padding: var(--theme-header-logo-padding, 0);
		border-radius: var(--theme-header-logo-radius, 0);
		overflow: hidden;
	}

	.theme-logo-page {
		display: flex;
		width: 100%;
	}

	.theme-logo-image {
		width: auto;
		max-width: 100%;
	}
</style>
