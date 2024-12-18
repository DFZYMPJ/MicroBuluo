$(document).ready(function(){
    $("#videocam").click(function(){
       
        $.ajax({
            url: "127.0.0.1:1316/manage", //要跳转的目标页面URL
            success: function(response) {
                window.location.href = response; //成功后重定向到目标页面
            },
            error: function(xhr, status, error) {
                console.log("发生错误：" + error);
            }
            });
        })

        $("#call_end").click(function(){
            $(function(){
            $(".call_page",window.parent.document).fadeIn('slow',function(){
                //隐藏通话界面
                $(".call_page").css('display','none')
            });
        })
        })
})