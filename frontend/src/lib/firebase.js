import { initializeApp } from 'firebase/app';
import { browserLocalPersistence, getAuth, GoogleAuthProvider, setPersistence } from 'firebase/auth';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
  apiKey: process.env.REACT_APP_FIREBASE_API_KEY,
  authDomain: process.env.REACT_APP_FIREBASE_AUTH_DOMAIN,
  projectId: process.env.REACT_APP_FIREBASE_PROJECT_ID,
  storageBucket: process.env.REACT_APP_FIREBASE_STORAGE_BUCKET,
  messagingSenderId: process.env.REACT_APP_FIREBASE_MESSAGING_SENDER_ID,
  appId: process.env.REACT_APP_FIREBASE_APP_ID,
};

const requiredVars = Object.entries(firebaseConfig)
  .filter(([, value]) => !value)
  .map(([key]) => key);

if (requiredVars.length > 0) {
  throw new Error(`Missing Firebase environment variables: ${requiredVars.join(', ')}`);
}

const app = initializeApp(firebaseConfig, process.env.REACT_APP_FIREBASE_APP_NAME || 'cora-web');

export const auth = getAuth(app);
export const db = getFirestore(app);
export const googleProvider = new GoogleAuthProvider();
export const authReady = setPersistence(auth, browserLocalPersistence).catch((error) => {
  console.error('Erro ao configurar persistencia do Firebase Auth:', error);
});

googleProvider.setCustomParameters({
  prompt: 'select_account',
});

export default app;
