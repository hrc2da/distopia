import { CONFIG } from "./config.js";
// Your web app's Firebase configuration
// Initialize Firebase
firebase.initializeApp(CONFIG);
console.log('initialized firebase');

export function writeLog(State) {
  "writing log to datbase"
  var newPostKey = firebase.database().ref().child('sessions').push().key;
  firebase.database().ref('sessions/' + State.sessionID).push({
    State
  });
}