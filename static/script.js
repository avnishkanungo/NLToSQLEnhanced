let isRecording = false;
let socket;
let microphone;

const socket_port = 5001;
socket = io(
  "http://" + window.location.hostname + ":" + socket_port.toString()
);

const tts_socket_port = 5002;
const tts_socket = io(
  "http://" + window.location.hostname + ":" + tts_socket_port.toString()
);

tts_socket.on("connect", () => {
  console.log("TTS: Connected to server");
});

let audioChunks = [];
const blob = new Blob(audioChunks, { type: "audio/wav" });
const audioContext = new AudioContext();

socket.on("transcription_update", (data) => {
  document.getElementById("captions").innerHTML = data.transcription;
});

socket.on("query_result", (data) => {
  document.getElementById("queryResult").innerHTML = marked.parse(data.result);
});

tts_socket.on("tts_audio_chunk", (data) => {
  // const blob = event.data
  console.log("TTS: Play button clicked! Add your audio playback logic. data:", data);
  audioChunks.push(new Uint8Array(data));
  
});

tts_socket.on("tts_audio_done", () => {
  console.log("TTS: Audio done");
  const blob = new Blob(audioChunks, { type: "audio/wav" });
  audioChunks = [];
  const audioUrl = URL.createObjectURL(blob);
  const audio = new Audio(audioUrl);
  audio.play();
  // const blob = new Blob(audioChunks, { type: "audio/wav" });
  // if (window.MediaSource) {
  //   console.log('MP4 audio is supported');
  //   const audioContext = new AudioContext();

  //   const reader = new FileReader();
  //   reader.onload = function () {
  //     const arrayBuffer = this.result;
  //     audioContext.decodeAudioData(arrayBuffer, (buffer) => {
  //       const source = audioContext.createBufferSource();
  //       source.buffer = buffer;
  //       source.connect(audioContext.destination);
  //       source.start();

  //       source.onended = () => {
  //         audioChunks = [];
  //       }
  //     })
  //   }
  //   reader.readAsArrayBuffer(blob);
  // } else {
  //   console.log('MP4 audio is not supported');
  // }
  // audioChunks = [];
});

// socket.on("play_query_result", (data) => {
//   document.getElementById("queryResult").innerHTML = marked.parse(data.result);
// });

async function getMicrophone() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    return new MediaRecorder(stream, { mimeType: "audio/webm" });
  } catch (error) {
    console.error("Error accessing microphone:", error);
    throw error;
  }
}

async function openMicrophone(microphone, socket) {
  return new Promise((resolve) => {
    microphone.onstart = () => {
      console.log("Client: Microphone opened");
      document.body.classList.add("recording");
      resolve();
    };
    microphone.ondataavailable = async (event) => {
      console.log("client: microphone data received");
      if (event.data.size > 0) {
        socket.emit("audio_stream", event.data);
      }
    };
    microphone.start(1000);
  });
}

async function startRecording() {
  isRecording = true;
  microphone = await getMicrophone();
  console.log("Client: Waiting to open microphone");
  await openMicrophone(microphone, socket);
}

async function stopRecording() {
  if (isRecording === true) {
    microphone.stop();
    microphone.stream.getTracks().forEach((track) => track.stop()); // Stop all tracks
    socket.emit("toggle_transcription", { action: "stop" });
    microphone = null;
    isRecording = false;
    console.log("Client: Microphone closed");
    document.body.classList.remove("recording");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const recordButton = document.getElementById("record");
  const runQueryButton = document.getElementById("runQuery");
  const playAudioButton = document.getElementById("playAudio");
  recordButton.addEventListener("click", () => {
    if (!isRecording) {
      socket.emit("toggle_transcription", { action: "start" });
      startRecording().catch((error) =>
        console.error("Error starting recording:", error)
      );
    } else {
      stopRecording().catch((error) =>
        console.error("Error stopping recording:", error)
      );
    }
  });

  runQueryButton.addEventListener("click", () => {
    const transcription = document.getElementById("captions").innerText;
    if (transcription && transcription !== "Realtime speech transcription API") {
      socket.emit("run_query", { question: transcription });
    } else {
      document.getElementById("queryResult").innerHTML = "Please record some speech first.";
    }
  });

  playAudioButton.addEventListener("click", () => {
    // alert("Play button clicked! Add your audio playback logic.");
    const queryResult = document.getElementById("queryResult").innerText;
    // const blob = new Blob(audioChunks, { type: "audio/wav" });
    // const audioContext = new AudioContext();

    tts_socket.emit("play_query_result", { result: queryResult });
    
    // tts_socket.on("message", (event) => {
    //   const blob = event.data
    //   audioChunks.push(blob);
    //   console.log("TTS: Play button clicked! Add your audio playback logic. data:", audioChunks);
    // });

    // if (event.data instanceof Blob) {
    //   const blob = event.data;
    //   audioChunks.push(blob);
    // }
    // tts_socket.on("tts_audio_chunk", (data) => {
    //   audioChunks.push(blob);
    // });
    // tts_socket.on("tts_audio_done", () => {
    //   const blob = new Blob(audioChunks, { type: "audio/wav" });
    //   audioChunks = [];
    //   const audioUrl = URL.createObjectURL(blob);
    //   const audio = new Audio(audioUrl);
    //   audio.play();
    // });
    
  });
});
