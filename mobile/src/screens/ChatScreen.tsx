import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  KeyboardAvoidingView,
  Platform,
  Text,
  TouchableOpacity,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { ChatBubble } from '../components/ChatBubble';
import { ChatInput } from '../components/ChatInput';
import { Message, sendMessage, healthCheck } from '../api/chat';

export function ChatScreen() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(false);
  const [connected, setConnected] = useState<boolean | null>(null);
  const [showMetadata, setShowMetadata] = useState(false);
  const flatListRef = useRef<FlatList>(null);

  // Check server connection on mount
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = async () => {
    const isHealthy = await healthCheck();
    setConnected(isHealthy);
    
    if (isHealthy && messages.length === 0) {
      // Welcome message
      setMessages([
        {
          id: 'welcome',
          role: 'assistant',
          content: '¡Hola! 🍞 Soy el asistente de la panadería. ¿En qué puedo ayudarte hoy?\n\nPuedes preguntarme sobre:\n• Precios y promociones\n• Horarios y ubicaciones\n• Hacer o consultar pedidos\n• Recomendaciones de productos',
          timestamp: new Date(),
        },
      ]);
    }
  };

  const handleSend = async (text: string) => {
    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: text,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);
    setLoading(true);

    try {
      const response = await sendMessage(text);
      
      // Add assistant response
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: response.response,
        timestamp: new Date(),
        metadata: {
          function_name: response.selected_function.name,
          score: response.selected_function.score,
        },
      };
      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      // Add error message
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: '❌ Lo siento, hubo un error al conectar con el servidor. Por favor, intenta de nuevo.',
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errorMessage]);
      setConnected(false);
    } finally {
      setLoading(false);
    }
  };

  const renderItem = ({ item }: { item: Message }) => (
    <ChatBubble message={item} showMetadata={showMetadata} />
  );

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <Text style={styles.headerTitle}>🥐 Panadería IA</Text>
          <View style={styles.statusContainer}>
            <View
              style={[
                styles.statusDot,
                connected === null
                  ? styles.statusLoading
                  : connected
                  ? styles.statusOnline
                  : styles.statusOffline,
              ]}
            />
            <Text style={styles.statusText}>
              {connected === null ? 'Conectando...' : connected ? 'En línea' : 'Desconectado'}
            </Text>
          </View>
        </View>
        
        <TouchableOpacity
          style={styles.metadataToggle}
          onPress={() => setShowMetadata(!showMetadata)}
        >
          <Ionicons
            name={showMetadata ? 'code-slash' : 'code-slash-outline'}
            size={22}
            color={showMetadata ? '#007AFF' : '#8E8E93'}
          />
        </TouchableOpacity>
      </View>

      {/* Chat Messages */}
      <KeyboardAvoidingView
        style={styles.chatContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={0}
      >
        <FlatList
          ref={flatListRef}
          data={messages}
          renderItem={renderItem}
          keyExtractor={item => item.id}
          contentContainerStyle={styles.messagesList}
          onContentSizeChange={() => flatListRef.current?.scrollToEnd({ animated: true })}
          onLayout={() => flatListRef.current?.scrollToEnd({ animated: false })}
        />

        <ChatInput onSend={handleSend} loading={loading} disabled={!connected} />
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
    backgroundColor: '#FAFAFA',
  },
  headerLeft: {
    flexDirection: 'column',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#1C1C1E',
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 2,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginRight: 6,
  },
  statusOnline: {
    backgroundColor: '#34C759',
  },
  statusOffline: {
    backgroundColor: '#FF3B30',
  },
  statusLoading: {
    backgroundColor: '#FF9500',
  },
  statusText: {
    fontSize: 12,
    color: '#8E8E93',
  },
  metadataToggle: {
    padding: 8,
  },
  chatContainer: {
    flex: 1,
  },
  messagesList: {
    paddingVertical: 12,
  },
});
