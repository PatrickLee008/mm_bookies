function noMultipleClicks(methods) {
    let that = this;
    
	if(typeof(that.noClick)=='undefined'){
		that.noClick = true;
	}
	
    if (that.noClick) {
        that.noClick= false;
        methods();
        setTimeout(function () {
            that.noClick= true;
        }, 2000)
    } 
}

//导出
export default {
	noMultipleClicks,//禁止多次点击
}