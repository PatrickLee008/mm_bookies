/*! *****************************************************************************
Copyright (c) Microsoft Corporation.

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES WITH
REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF MERCHANTABILITY
AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR ANY SPECIAL, DIRECT,
INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES WHATSOEVER RESULTING FROM
LOSS OF USE, DATA OR PROFITS, WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR
OTHER TORTIOUS ACTION, ARISING OUT OF OR IN CONNECTION WITH THE USE OR
PERFORMANCE OF THIS SOFTWARE.
***************************************************************************** */var i=function(o,t){return i=Object.setPrototypeOf||{__proto__:[]}instanceof Array&&function(n,r){n.__proto__=r}||function(n,r){for(var e in r)Object.prototype.hasOwnProperty.call(r,e)&&(n[e]=r[e])},i(o,t)};function s(o,t){if(typeof t!="function"&&t!==null)throw new TypeError("Class extends value "+String(t)+" is not a constructor or null");i(o,t);function n(){this.constructor=o}o.prototype=t===null?Object.create(t):(n.prototype=t.prototype,new n)}var u=function(){function o(t){this.colorStops=t||[]}return o.prototype.addColorStop=function(t,n){this.colorStops.push({offset:t,color:n})},o}();const f=u;var p=function(o){s(t,o);function t(n,r,e,l,c){var a=o.call(this,l)||this;return a.x=n==null?.5:n,a.y=r==null?.5:r,a.r=e==null?.5:e,a.type="radial",a.global=c||!1,a}return t}(f);const d=p;export{f as G,d as R,s as _};
