
/*

message Object

使用默认值
{
    loading: false, // 如果想显示三个动点的加载动画请设置为true。仅在 >= 0.3.1版本。
  
    delay: 0, // 延迟显示消息，单位为毫秒。
  
    type: 'text', // 可以为 'text' 或 'embed'
  
    content: '', // 若上述类型为 'embed' 应为URL, 否则应为文本。
  
    human: false, // 右对齐。
  
    cssClass: '', //  一个或一组class类名。
  }

  */



$(document).ready(function(){

  function setCookie(cname,cvalue,exdays){
    var d = new Date();
    d.setTime(d.getTime()+(exdays*24*60*60*1000));
    var expires = "expires="+d.toGMTString();
    document.cookie = cname+"="+cvalue+"; "+expires;
  }

  function getCookie(cname){
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for(var i=0; i<ca.length; i++) {
      var c = ca[i].trim();
      if (c.indexOf(name)==0) { return c.substring(name.length,c.length); }
    }
    return "";
  }

    //创建聊天对话
    var chatui = new BotUI('ChatContent'),
    address = '192.168.0.103:5000';//地址变量

    //创建SocketIO
    var socket = io()

    //socket第一次握手连接
    socket.on('connect',function(){
       //向服务器发送信息
       socket.send('客户端已连接！');
      
       
   });

   //socket第三次握手连接
   socket.on('message',function(msg,cb){
    //接收服务器响应的消息
    setCookie('sid',msg.sid,1)  
   });
   if(getCookie('nickname') == '' && getCookie('roomNum') == ''){
    document.cookie = "nickname=;Max-Age=0";
   }

   if(getCookie('nickname') == '' || getCookie('roomNum') == ''){
    FaceChatO()
   }else{
    FaceChatT()
   }

   function FaceChatT(){
    //如果已经登陆时与用户交互
    chatui.message.bot('感谢你再次访问它！').then(function(){
       //更新上一条消息
       chatui.message.add({
        loading:true,
        delay:1000,
        content: '你的昵称：' + getCookie('nickname')
       })
      chatui.message
      .add({
      loading:true,
      delay:1000,
      content:'房间口令:【<span style="color:blue;">'+ getCookie('roomNum') +'</span>】'
      }).then(function(index){
        setTimeout(function(){
          chatui.message.update(index,{
            content:'重复登录了！' 
          })
        },10000)
      }); 
      chatui.action.button({
        loading:true,
        delay:2000,
        addMessage: true,
        action: [
          { 
            icon:'check',
            text: '继续',
            value: 'continue'
          },{
            text:'结束',
            value:'break'
          }
        ]
      }).then(function (res) { // 点击按钮会回调

        if(res.value == 'continue'){
        FaceChatO()
        //socket发送joinRoom的给服务器
        socket.emit('joinRoom',{
          room:getCookie('nickname'),
          username:getCookie('roomNum'),
        });
        }else{
          // NO表示不加入房间,清空cookie
          document.cookie = "nickname=; Max-Age=0";
          document.cookie = "roomNum=; Max-Age=0";
          window.location.reload(true);
        }
      });
    })
   }
   
   function FaceChatO(){
   //创建账户时与用户交互
    chatui.message
    .bot('这是一个即时通讯系统！\n你可以通过它与你的朋友聊天,视频通话。')
    .then(function(index){
      chatui.message.bot({
        loading:true,
        delay:1000,
        human:false,
        content:'开始面对面对话之前，我需要知道你的名字？'
      }).then(function(index){
        return chatui.action.text({
          loading:true,
          delay:1000,
          addMessage: true,
          action:{
            sub_type:'text',
            placeholder:'What you name?',
            value:getCookie('nickname')
          }
        }).then(function(res){
          console.log(res.value);
          setCookie('nickname',res.value,1)
         
          chatui.message
          .add({
            type:'text',
            loading:true,
            delay:200,
            content:'我记住了！你的名字叫' + res.value
          }).then(function(index){
            //两秒后更新上一条消息
            setTimeout(function(){
              chatui.message.update(index,{
                content:'感谢你提供这个信息！'
              })
            },5000)
          })
         
      })
    }).then(function(){
      
      chatui.message
            .add({
              loading:true,
              delay:1500,
              content:'你要注册的口令是什么？'
            }).then(function(){
              //
            })
        chatui.action.text({
            delay:1000,
            loading:true,
            addMessage: true,
            action:{
              sub_type:'text',
              placeholder:'Register password!',
              value:getCookie('roomNum')
            }
          }).then(function(room){
            //保存用户输入房间ID时的cookies
            setCookie('roomNum',room.value,1)
            var nickname = getCookie('nickname')
            //socket发送joinRoom的给服务器
            socket.emit('joinRoom',{
              room:room.value,
              username:nickname,
            });
          });
    })
  
  })
}

    //加入房间
    socket.on('roomJoined',function(msg,cb){
       chatui.message.add({
        loading:true,
        delay:1000,
        human:false,
        content:'播报消息:热烈欢迎‘' + msg.username + '’已加入‘' + msg.room + '’群组' 
       })
       sendMessage();
    });

     //发送消息输入框
  function sendMessage(){
    chatui.action.text({
      delay:500,
      action:{
        type:'text',
        placeholder:'input Message'
      }
    }).then(function(res){
      console.log(res)
      socket.emit('sendMsg',{
        msg:res.value,
        sid:getCookie('sid'),
        username:getCookie('nickname'),
        room:getCookie('roomNum')
      })
    })
}

    //用户离开房间时通知聊天室里的人
    socket.on('roomLeft',function(msg,cb){
      chatui.message.add({
        loading:true,
        delay:1000,
        human:false,
        content:msg.username + '已注销' + msg.room
       });
    })
    //判断下一步操作
      function chonse(){
        chatui.action.button({
          addMessage: false,
          action: [
            { 
              icon:'paper-plane',
              text: '发消息',
              value: 'sendMsg'
            },
            {
              icon:'phone-volume',
              text:'视频通话',
              value:'videoChat'
            }
            ,
            {
              icon:'sign-out',
              text:'离开',
              value:'exit'
            }
          ]
        }).then(function(res){
          if(res.value == 'sendMsg'){
            sendMessage();
          }
          if(res.value == 'videoChat'){
            //发起视频通话
            socket.emit('joinVideoChat',{
              sid:getCookie('sid'),
              room:getCookie('roomNum'),
              name:getCookie('nickname')
            })
            RoomVideo(getCookie('nickname'),getCookie('roomNum'))
          }
          if(res.value == 'exit'){
            //离开房间
            socket.emit('leaveRoom',{
              msg:res.value,
              username:getCookie('nickname'),
              room:getCookie('roomNum')
            })

             //用户离开房间时通知他个人
            socket.on('roomLeftPersonal',function(msg,cb){
              chatui.message.add({
              loading:true,
              delay:1000,
              human:false,
              content:'你已退出' + msg.room
              });
              //重新加入面对面聊天
              FaceChat();
          })
          //清空cookie,
          document.cookie = "nickname=; Max-Age=0";
          document.cookie = "roomNum=; Max-Age=0";
          }
        })
      }
        //广播消息，在同一房间的用户都会收到
        socket.on('SendToAll',function(msg,cb){
          if(msg.sid == getCookie('sid')){
           chonse()
          }else{
            //消息震动
            navigator.vibrate([1000,500])
            const audioCtx = new AudioContext();
            // 创建正弦波
            const oscillator = audioCtx.createOscillator();
            oscillator.type = 'sine'; // 选择正弦波作为波形类型
            oscillator.frequency.value = 20; // 设置频率值
             
            // 连接正弦波到输出设备
            oscillator.connect(audioCtx.destination);
             
                  // 开始发生震动效果
                      oscillator.start();
            
                        setTimeout(function(){
                          oscillator.stop();
                        },2000)
            
            chatui.message.add({
              type:msg.type,
               loading:true,
               delay:1000,
               human:false,
               content:msg.username + ':' + msg.msg
              })
          }
        });
        function called(){
          $(function(){
            $(".call_page",window.parent.document).fadeIn('slow',function(){
                //隐藏通话界面
                $(".call_page").css('display','none')
                navigator.vibrate([500,500])
            });
        })
        }
        $("#call_end").click(function(){
          called()
      })
        // 接受视频通话
      $("#videocam").click(function(){
        navigator.vibrate([500,500])
        called()
        RoomVideo(getCookie('nickname'),getCookie('roomNum'))
      })
        //  跳转到视频通话页面
      function RoomVideo(name,room){
              var protocol = window.location.protocol;
              url = protocol + '//' + document.domain + ':' + '8080' + '/videoChat?room_id='+ room + '&display_name=' + name + '&mute_video=0&mute_audio=0';
              window.open(url);
        }
        //视频来电通知页面
        socket.on('roomVideoChat',function(msg,cb){
          //来电者的昵称
          $("#videoNickname").text(msg.name)
          if(msg.sid == getCookie('sid')){
              console.log('房间里有人发起视频通话！')
              chonse();
              RoomVideo(msg.name,msg.room)
          }else{
            chatui.message.add({
              loading:true,
              delay:1000,
              human:false,
              content:msg.name + '发起通话连接！'
           }).then(function(){
              $(function(){
                $(".call_page",window.parent.document).fadeIn('slow',function(){
                  //来电震动
                  navigator.vibrate([2000,1000,3000,1000,2000,1000,3000,1000,2000,1000,3000,1000,4000])
                    
                    //显示通话动画
                    $(".call_page").css('display','flex')
                    //20s后隐藏通知
                    setTimeout(function(){
                      //不接通20S后隐藏通知
                      $(".call_page").css('display','none')
                    },20000)
                    setTimeout(function(){
                      chonse()
                    },1000)
                });
                
            })
              
           })
          }
      
        })
});