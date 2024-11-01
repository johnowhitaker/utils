const videoElement = document.getElementById('webcam');
const canvasElement = document.getElementById('overlay');
const canvasCtx = canvasElement.getContext('2d');
const handLevelBar = document.getElementById('handLevel');
const mouthLevelBar = document.getElementById('mouthLevel');
const restingPositionBtn = document.getElementById('restingPositionBtn');
const countdownElement = document.getElementById('countdown');
const midiOutputSelect = document.getElementById('midiOutputSelect');

let handRestingHeight = null;
let mouthRestingOpenness = null;
let midiAccess = null;
let midiOutput = null;

// Variables to store last positions
let lastHandHeight = 0;
let lastMouthOpenness = 0;

// Which CC codes to use
const handCC = 111;
const mouthCC = 113;

// Initialize Webcam
async function initCamera() {
  const stream = await navigator.mediaDevices.getUserMedia({ video: true });
  videoElement.srcObject = stream;
  await videoElement.play();

  // Adjust canvas size
  canvasElement.width = videoElement.videoWidth;
  canvasElement.height = videoElement.videoHeight;
}

// Initialize MIDI
async function initMIDI() {
  if (navigator.requestMIDIAccess) {
    midiAccess = await navigator.requestMIDIAccess();
    populateMIDIOutputs();
    midiAccess.onstatechange = populateMIDIOutputs;
  } else {
    console.warn('Web MIDI API not supported in this browser.');
  }
}

// Populate MIDI Output Devices
function populateMIDIOutputs() {
  midiOutputSelect.innerHTML = '';
  if (midiAccess && midiAccess.outputs.size > 0) {
    midiAccess.outputs.forEach((output) => {
      const option = document.createElement('option');
      option.value = output.id;
      option.textContent = output.name;
      midiOutputSelect.appendChild(option);
    });
    // Set the first output as default
    midiOutput = midiAccess.outputs.get(midiOutputSelect.value);
  } else {
    const option = document.createElement('option');
    option.textContent = 'No MIDI Outputs';
    midiOutputSelect.appendChild(option);
  }
}

// MIDI Output Selection Change
midiOutputSelect.addEventListener('change', () => {
  midiOutput = midiAccess.outputs.get(midiOutputSelect.value);
});

// Send MIDI Control Change
function sendMIDIControl(controlNumber, value) {
  if (midiOutput) {
    midiOutput.send([0xB0, controlNumber, value]);
  }
}

// Initialize Mediapipe Hands
const hands = new Hands({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/hands/${file}` });
hands.setOptions({
  maxNumHands: 2,
  modelComplexity: 1,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.7,
});

// Initialize Mediapipe Face Mesh
const faceMesh = new FaceMesh({ locateFile: (file) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${file}` });
faceMesh.setOptions({
  maxNumFaces: 1,
  refineLandmarks: true,
  minDetectionConfidence: 0.7,
  minTrackingConfidence: 0.7,
});

// Combined Results Processing
async function onResults() {
  // Process hands
  await hands.send({ image: videoElement });
  // Process face
  await faceMesh.send({ image: videoElement });
}

// Hands Results Callback
hands.onResults((results) => {
  canvasCtx.save();
  canvasCtx.clearRect(0, 0, canvasElement.width, canvasElement.height);
  canvasCtx.drawImage(results.image, 0, 0, canvasElement.width, canvasElement.height);

  if (results.multiHandLandmarks && results.multiHandLandmarks.length > 0) {
    let maxHandY = 1; // Start with bottom of the screen
    results.multiHandLandmarks.forEach((landmarks) => {
      // Draw hand landmarks
      drawConnectors(canvasCtx, landmarks, HAND_CONNECTIONS, { color: '#00FF00', lineWidth: 2 });
      drawLandmarks(canvasCtx, landmarks, { color: '#FF0000', lineWidth: 1 });

      landmarks.forEach((point) => {
        maxHandY = Math.min(maxHandY, point.y); // Get the highest point (smallest y)
      });
    });

    let handHeight = 1 - maxHandY; // Invert y-axis for screen coordinates
    lastHandHeight = handHeight;

    if (handRestingHeight !== null) {
      handHeight = handHeight - handRestingHeight;
    }

    // Clamp and scale MIDI value
    let midiValue = Math.floor(handHeight * 127);
    midiValue = Math.max(0, Math.min(midiValue, 127));
    sendMIDIControl(handCC, midiValue); // Control change 1

    // Update level bar
    handLevelBar.style.setProperty('--level', `${(midiValue / 127) * 100}%`);
  } else {
    // No hands detected
    handLevelBar.style.setProperty('--level', '0%');
  }

  canvasCtx.restore();
});

// Face Results Callback
faceMesh.onResults((results) => {
  canvasCtx.save();

  if (results.multiFaceLandmarks && results.multiFaceLandmarks.length > 0) {
    const faceLandmarks = results.multiFaceLandmarks[0];
    // Draw face landmarks
    drawConnectors(canvasCtx, faceLandmarks, FACEMESH_TESSELATION, { color: '#C0C0C070', lineWidth: 1 });

    // Mouth openness calculation
    const upperLip = faceLandmarks[13];
    const lowerLip = faceLandmarks[14];
    let mouthOpenness = Math.abs(upperLip.y - lowerLip.y);
    lastMouthOpenness = mouthOpenness;

    if (mouthRestingOpenness !== null) {
      mouthOpenness = mouthOpenness - mouthRestingOpenness;
    }

    // Clamp and scale MIDI value
    let midiValue = Math.floor(mouthOpenness * 2000); // Scale factor may need adjustment
    midiValue = Math.max(0, Math.min(midiValue, 127));
    sendMIDIControl(mouthCC, midiValue); // Control change 2

    // Update level bar
    mouthLevelBar.style.setProperty('--level', `${(midiValue / 127) * 100}%`);
  } else {
    // No face detected
    mouthLevelBar.style.setProperty('--level', '0%');
  }

  canvasCtx.restore();
});

// Start Camera Feed
const camera = new Camera(videoElement, {
  onFrame: async () => {
    await onResults();
  },
  width: 640,
  height: 480,
});

// Resting Position Calibration
restingPositionBtn.addEventListener('click', () => {
  let countdown = 3;
  countdownElement.textContent = countdown;
  const interval = setInterval(() => {
    countdown--;
    countdownElement.textContent = countdown;
    if (countdown === 0) {
      clearInterval(interval);
      countdownElement.textContent = '';
      handRestingHeight = lastHandHeight || 0;
      mouthRestingOpenness = lastMouthOpenness || 0;
    }
  }, 1000);
});

// Initialize everything
initCamera().then(() => {
  camera.start();
  initMIDI();
});
