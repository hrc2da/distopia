import { CONFIG } from "./config.js";
// Your web app's Firebase configuration
// Initialize Firebase
firebase.initializeApp(CONFIG);
console.log('initialized firebase');
firebase.analytics();

var database = firebase.database();

export function writeLog() {
console.log('calling writE LOG')
  firebase.database().ref().set({
    log: "hello"
  });
}