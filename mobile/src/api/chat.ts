// API client para conectar con el backend FastAPI
import { Platform } from 'react-native';

// ⚠️ CAMBIA ESTA IP por la de tu computadora en la red local
// Ejecuta 'ipconfig' en Windows o 'ifconfig' en Mac/Linux para encontrarla
const LOCAL_PC_IP = '192.168.10.165';

const getBaseUrl = () => {
  // Web: usa localhost
  if (Platform.OS === 'web') {
    return 'http://localhost:8000';
  }
  // Android emulator: usa 10.0.2.2 (mapea a localhost del host)
  if (Platform.OS === 'android' && __DEV__) {
    // Detectar si es emulador o dispositivo físico
    // En dispositivo físico, usar IP local
    return `http://${LOCAL_PC_IP}:8000`;
  }
  // iOS simulator o dispositivo físico: usar IP local
  return `http://${LOCAL_PC_IP}:8000`;
};

export interface ChatResponse {
  session_id: string;
  query: string;
  selected_function: {
    name: string;
    score: number;
  };
  plan: Array<{
    step: number;
    tool: string;
    args: Record<string, unknown>;
  }>;
  exec_log: string[];
  response: string;
}

export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  metadata?: {
    function_name?: string;
    score?: number;
  };
}

export async function sendMessage(
  query: string, 
  sessionId: string = 'default-session'
): Promise<ChatResponse> {
  const response = await fetch(`${getBaseUrl()}/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json; charset=utf-8',
    },
    body: JSON.stringify({
      session_id: sessionId,
      query: query,
    }),
  });

  if (!response.ok) {
    throw new Error(`Error ${response.status}: ${response.statusText}`);
  }

  return response.json();
}

export async function healthCheck(): Promise<boolean> {
  try {
    const response = await fetch(`${getBaseUrl()}/health`);
    const data = await response.json();
    return data.ok === true;
  } catch {
    return false;
  }
}
