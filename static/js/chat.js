$(document).ready(function(){
    //define all messages classes accordingly
    var user = $("#username").text();
    console.log("user is")
    console.log(user)
    var all_msg = $("#chatbox > ."+user+"_msg");
  
    for(var i=0; i<all_msg.length; i++){
        var msg_div = all_msg[i];
        msg_div.classList.add("user")
        
    } 

    //deals with socket
    var socket = io.connect("http://127.0.0.1:5000/");

    socket.on("connect", function(){
        console.log("Conectado")
        socket.emit("system_msg", user+" se conectou")
    });

    function display_msg(msg){
        $("#chatbox").append(msg);
        scroll();
    }

    function scroll(){
        var chatbox = document.getElementById("chatbox")
        chatbox.scrollTop = chatbox.scrollHeight - chatbox.clientHeight;
    }

    socket.on("message", function(msg_dict){
        console.log(msg_dict);
        if(msg_dict["user"]==user){
            var msg = "<div class=user>("
        }else{
            var msg = "<div class=other_user>("
        }
        msg += msg_dict["date"]+")["+msg_dict["user"]+"]:"+msg_dict["message"]+"</div>";
        display_msg(msg);
    });

    socket.on("invalid_msg", function(notification){
        $("#notification").text(notification);
    })

    socket.on("system", function(msg){
        console.log(msg);
        var msg = "<div class=system>~"+msg+"~</div>";
        display_msg(msg);
    });

    socket.on("clear", function(unimportant){//clear msg input
        $("#msg_input").val("")
    })

    function send_msg(){
        $("#notification").text("");
        socket.emit("message", [user, $("#msg_input").val()])
    }

    $("#send_input").click(send_msg)//send msg
    document.getElementById("msg_input").addEventListener("keydown", function(event){//enter also sends msg
        if(event.keyCode === 13){
            send_msg()
        }
    })


});