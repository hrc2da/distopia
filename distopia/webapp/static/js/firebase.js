import { CONFIG } from "./config.js";
// Your web app's Firebase configuration
// Initialize Firebase
firebase.initializeApp(CONFIG);
console.log('initialized firebase');

export function writeLog() {
console.log('calling writE LOG')
  firebase.database().ref().set({
    log: "hello"
  });
}