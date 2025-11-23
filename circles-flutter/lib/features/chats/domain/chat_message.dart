class ChatMessage {
  ChatMessage({
    required this.id,
    required this.senderId,
    required this.text,
    required this.sentAt,
    this.receiverId,
  });

  final String id;
  final String senderId;
  final String? receiverId;
  final String text;
  final DateTime sentAt;

  factory ChatMessage.fromApi(Map<String, dynamic> json) {
    final sentAtRaw = json['createdAt'] ?? json['sentAt'];
    return ChatMessage(
      id: (json['id'] ?? '').toString(),
      senderId: (json['senderUserId'] ?? json['senderId'] ?? '').toString(),
      receiverId: (json['receiverId'] ?? '').toString().isEmpty
          ? null
          : (json['receiverId'] ?? '').toString(),
      text: (json['content'] ?? json['text'] ?? '').toString(),
      sentAt: sentAtRaw is String
          ? DateTime.tryParse(sentAtRaw) ??
              DateTime.fromMillisecondsSinceEpoch(0)
          : DateTime.fromMillisecondsSinceEpoch(0),
    );
  }
}
