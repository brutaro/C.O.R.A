import {
  collection,
  deleteDoc,
  doc,
  getDoc,
  getDocs,
  increment,
  orderBy,
  query,
  serverTimestamp,
  setDoc,
  updateDoc,
  writeBatch,
} from 'firebase/firestore';
import { db } from './firebase';

const ASSISTANT_NAME = 'C.O.R.A.';
const ASSISTANT_SLUG = 'cora';
const KNOWLEDGE_NAMESPACE = 'notas_conflito_interesse';

function userDocRef(uid) {
  return doc(db, 'users', uid);
}

function conversationsCollectionRef(uid) {
  return collection(db, 'users', uid, 'conversations');
}

function conversationDocRef(uid, conversationId) {
  return doc(db, 'users', uid, 'conversations', conversationId);
}

function messagesCollectionRef(uid, conversationId) {
  return collection(db, 'users', uid, 'conversations', conversationId, 'messages');
}

function serializeTimestamp(value) {
  if (!value) {
    return null;
  }

  if (typeof value.toDate === 'function') {
    return value.toDate().toISOString();
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  return value;
}

export async function ensureUserProfile(user) {
  if (!user?.uid) {
    throw new Error('Usuário Firebase não encontrado');
  }

  const existingProfile = await getDoc(userDocRef(user.uid));
  const basePayload = {
    uid: user.uid,
    email: user.email || '',
    display_name: user.displayName || user.email || 'Usuário',
    photo_url: user.photoURL || null,
    provider: 'google',
    status: 'active',
    last_login_at: serverTimestamp(),
    updated_at: serverTimestamp(),
  };

  await setDoc(
    userDocRef(user.uid),
    existingProfile.exists()
      ? basePayload
      : {
          ...basePayload,
          created_at: serverTimestamp(),
        },
    { merge: true }
  );
}

export async function listConversations(uid) {
  const snapshot = await getDocs(
    query(conversationsCollectionRef(uid), orderBy('updated_at', 'desc'))
  );

  return snapshot.docs.map((conversationDoc) => {
    const data = conversationDoc.data();
    return {
      id: conversationDoc.id,
      title: data.title || 'Nova conversa',
      updated_at: serializeTimestamp(data.updated_at),
      created_at: serializeTimestamp(data.created_at),
      last_message_at: serializeTimestamp(data.last_message_at),
      message_count: data.message_count || 0,
    };
  });
}

export async function createConversation(user, title = 'Nova conversa') {
  const conversationRef = doc(conversationsCollectionRef(user.uid));

  await setDoc(conversationRef, {
    conversation_id: conversationRef.id,
    title,
    assistant_slug: ASSISTANT_SLUG,
    assistant_name: ASSISTANT_NAME,
    knowledge_namespace: KNOWLEDGE_NAMESPACE,
    status: 'active',
    message_count: 0,
    created_at: serverTimestamp(),
    updated_at: serverTimestamp(),
    last_message_at: serverTimestamp(),
  });

  return {
    id: conversationRef.id,
    title,
  };
}

export async function renameConversation(uid, conversationId, title) {
  await updateDoc(conversationDocRef(uid, conversationId), {
    title,
    updated_at: serverTimestamp(),
  });
}

export async function addMessage(uid, conversationId, role, content, metadata = {}) {
  const messageRef = doc(messagesCollectionRef(uid, conversationId));
  const batch = writeBatch(db);

  batch.set(messageRef, {
    message_id: messageRef.id,
    role,
    content,
    metadata,
    created_at: serverTimestamp(),
    status: 'saved',
  });

  batch.update(conversationDocRef(uid, conversationId), {
    updated_at: serverTimestamp(),
    last_message_at: serverTimestamp(),
    message_count: increment(1),
  });

  await batch.commit();

  return messageRef.id;
}

export async function loadConversationMessages(uid, conversationId) {
  const snapshot = await getDocs(
    query(messagesCollectionRef(uid, conversationId), orderBy('created_at', 'asc'))
  );

  return snapshot.docs.map((messageDoc) => {
    const data = messageDoc.data();
    return {
      id: messageDoc.id,
      role: data.role,
      content: data.content,
      references: data.metadata?.references || [],
      timestamp: serializeTimestamp(data.created_at) || new Date().toISOString(),
      isError: data.status === 'error',
    };
  });
}

export async function updateConversationTitle(uid, conversationId, title) {
  await updateDoc(conversationDocRef(uid, conversationId), {
    title,
    updated_at: serverTimestamp(),
  });
}

export async function deleteConversation(uid, conversationId) {
  const messagesSnapshot = await getDocs(messagesCollectionRef(uid, conversationId));
  const messageRefs = messagesSnapshot.docs.map((messageDoc) => messageDoc.ref);
  const chunkSize = 400;

  for (let index = 0; index < messageRefs.length; index += chunkSize) {
    const batch = writeBatch(db);
    messageRefs.slice(index, index + chunkSize).forEach((messageRef) => {
      batch.delete(messageRef);
    });
    await batch.commit();
  }

  await deleteDoc(conversationDocRef(uid, conversationId));
}

export async function getConversation(uid, conversationId) {
  const snapshot = await getDoc(conversationDocRef(uid, conversationId));
  if (!snapshot.exists()) {
    return null;
  }

  const data = snapshot.data();
  return {
    id: snapshot.id,
    title: data.title || 'Nova conversa',
    updated_at: serializeTimestamp(data.updated_at),
  };
}
