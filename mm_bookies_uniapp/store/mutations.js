//保存用户信息
export const saveUserInfo = (state, userInfo) => {
  state.userInfo = userInfo;
};
 
// 保存公共配置参数
export const saveConfigs = (state, configs) => {
  state.configs = configs;
};

// 保存公共配置参数
export const savePageCur = (state, pageCur) => {
  state.pageCur = pageCur;
};

