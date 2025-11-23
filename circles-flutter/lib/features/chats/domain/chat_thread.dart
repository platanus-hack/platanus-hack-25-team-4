import 'chat_message.dart';

class ChatThread {
  ChatThread({
    required this.id,
    required this.personId,
    required this.personName,
    required this.circleObjective,
    required this.lastMessage,
    required this.unreadCount,
    required this.messages,
  });

  final String id;
  final String personId;
  final String personName;
  final String? circleObjective;
  final String? lastMessage;
  final int unreadCount;
  final List<ChatMessage> messages;

  ChatThread copyWith({
    String? lastMessage,
    int? unreadCount,
    List<ChatMessage>? messages,
  }) {
    return ChatThread(
      id: id,
      personId: personId,
      personName: personName,
      circleObjective: circleObjective,
      lastMessage: lastMessage ?? this.lastMessage,
      unreadCount: unreadCount ?? this.unreadCount,
      messages: messages ?? this.messages,
    );
  }

  static ChatThread empty() => ChatThread(
        id: '',
        personId: '',
        personName: '',
        circleObjective: null,
        lastMessage: null,
        unreadCount: 0,
        messages: const [],
      );
}
