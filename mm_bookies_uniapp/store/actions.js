export const saveUserInfo = ({ commit }, userInfo) => {
  commit('saveUserInfo', userInfo);
};

export const saveConfigs = ({ commit }, configs) => {
  commit('saveConfigs', configs);
};

export const savePageCur = ({ commit }, pageCur) => {
  commit('savePageCur', pageCur);
};
