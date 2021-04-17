$(document).ready(function(){
    //define all messages classes accordingly
    var user = $("#user_input").val();
    var all_msg = $("#chatbox > ."+user+"_msg");
  
    for(var i=0; i<all_msg.length; i++){
        var msg_div = all_msg[i];
        msg_div.classList.add("user")
        
    } 

    //deals with socket
    var socket = io.connect("https://flask-chat-hikaridesuyoo.herokuapp.com/");

    socket.on("connect", function(){
        console.log("Conectado")
        socket.emit("system_msg", "Um usuário se conectou")
    });

    function display_msg(msg){
        $("#chatbox").append(msg);
        scroll();
    }

    function scroll(){
        var chatbox = document.getElementById("chatbox")
        chatbox.style.height = (window.screen.height-parseInt(window.screen.height/2.6)).toString()+'px';
        chatbox.scrollTop = chatbox.scrollHeight - chatbox.clientHeight;
    }

    socket.on("message", function(msg_dict){
        console.log(msg_dict);
        user = $("#user_input").val()
        if(msg_dict["user"]==user){
            var msg = "<div class=user>("
        }else{
            var msg = "<div class=other_user>("
        }
        msg += msg_dict["date"]+")["+msg_dict["user"]+"]:"+msg_dict["message"]+"</div>";
        display_msg(msg);
    });

    socket.on("system", function(msg){
        console.log(msg);
        var msg = "<div class=system>~"+msg+"~</div>";
        display_msg(msg);
    });

    socket.on("clear", function(unimportant){//clear msg input
        $("#msg_input").val("")
    })

    function send_msg(){
        socket.emit("message", [$("#user_input").val(), $("#msg_input").val()])
    }

    $("#send_input").click(send_msg)//send msg
    document.getElementById("msg_input").addEventListener("keydown", function(event){//enter also sends msg
        if(event.keyCode === 13){
            send_msg()
        }
    })


});