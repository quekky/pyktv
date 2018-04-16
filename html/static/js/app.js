ons.ready(function() {
    var myTabbar = $("ons-tabbar")
    myTabbar.bind("prechange reactive", function(e) {
        pagename=e.originalEvent.tabItem.getAttribute('name')
        navigators=$("ons-navigator#"+pagename+"Navigator")
        if(navigators.length>0 && navigators[0].pages.length>1){
            opt={times:navigators[0].pages.length-1}
            if(e.originalEvent.type==='prechange') opt['animation']='none'
            navigators[0].popPage(opt)
        }
        $('ons-modal').hide()
    })

    if (ons.platform.isIPhoneX()) {
        // Add empty attribute to the <html> element
        document.documentElement.setAttribute('onsflag-iphonex-portrait', '');
        document.documentElement.setAttribute('onsflag-iphonex-landscape', '');
    }
})



function addvideo(item, index) {
    item=$(item).parent('ons-list-item')
    index=item.attr('index')
    $.get('/api/addvideo',{index:index})
    console.log(item.offset())
    clone=item.clone()
    clone.insertBefore(item)
        .addClass('list-helper')
        .offset(item.offset())
        .width(item.width())
        .addClass('movetoplaylist')
    setTimeout(function() {
        clone.remove()
    }, 1000)
}

function filterlist(list, filter) {
    flist=[]

}