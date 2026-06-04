//保存用户信息
export const saveUserInfo = (state, userInfo) => {
  state.userInfo = userInfo;
  // 同步缓存到本地，供时区转换等工具读取（含 timezone 字段）
  uni.setStorageSync('user_info', userInfo);
};
 
// 保存公共配置参数
export const saveConfigs = (state, configs) => {
  state.configs = configs;
};

// 保存公共配置参数
export const savePageCur = (state, pageCur) => {
  state.pageCur = pageCur;
};

