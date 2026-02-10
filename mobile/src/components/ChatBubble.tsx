import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Message } from '../api/chat';

interface ChatBubbleProps {
  message: Message;
  showMetadata?: boolean;
}

export function ChatBubble({ message, showMetadata = false }: ChatBubbleProps) {
  const isUser = message.role === 'user';

  return (
    <View style={[styles.container, isUser ? styles.userContainer : styles.assistantContainer]}>
      <View style={[styles.bubble, isUser ? styles.userBubble : styles.assistantBubble]}>
        <Text style={[styles.text, isUser ? styles.userText : styles.assistantText]}>
          {message.content}
        </Text>
        
        {showMetadata && message.metadata?.function_name && (
          <View style={styles.metadata}>
            <Text style={styles.metadataText}>
              📍 {message.metadata.function_name} ({(message.metadata.score! * 100).toFixed(1)}%)
            </Text>
          </View>
        )}
      </View>
      
      <Text style={[styles.timestamp, isUser ? styles.userTimestamp : styles.assistantTimestamp]}>
        {message.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginVertical: 4,
    marginHorizontal: 12,
    maxWidth: '80%',
  },
  userContainer: {
    alignSelf: 'flex-end',
  },
  assistantContainer: {
    alignSelf: 'flex-start',
  },
  bubble: {
    paddingVertical: 10,
    paddingHorizontal: 14,
    borderRadius: 18,
  },
  userBubble: {
    backgroundColor: '#007AFF',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: '#E9E9EB',
    borderBottomLeftRadius: 4,
  },
  text: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#FFFFFF',
  },
  assistantText: {
    color: '#000000',
  },
  timestamp: {
    fontSize: 11,
    marginTop: 4,
  },
  userTimestamp: {
    color: '#8E8E93',
    textAlign: 'right',
  },
  assistantTimestamp: {
    color: '#8E8E93',
    textAlign: 'left',
  },
  metadata: {
    marginTop: 6,
    paddingTop: 6,
    borderTopWidth: 1,
    borderTopColor: 'rgba(0,0,0,0.1)',
  },
  metadataText: {
    fontSize: 11,
    color: '#666',
    fontStyle: 'italic',
  },
});
