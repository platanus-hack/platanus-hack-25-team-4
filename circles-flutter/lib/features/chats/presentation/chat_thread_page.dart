import 'package:flutter/material.dart';

import '../../../core/widgets/app_logo.dart';
import '../../app/app_state.dart';
import '../domain/chat_message.dart';

class ChatThreadPage extends StatefulWidget {
  const ChatThreadPage({super.key, required this.chatId, required this.state});

  final String chatId;
  final AppState state;

  @override
  State<ChatThreadPage> createState() => _ChatThreadPageState();
}

class _ChatThreadPageState extends State<ChatThreadPage> {
  late final TextEditingController _controller;

  @override
  void initState() {
    super.initState();
    _controller = TextEditingController();
    widget.state.loadMessagesForChat(widget.chatId).then((_) {
      if (mounted) setState(() {});
    }).catchError((_) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('No pudimos cargar los mensajes.')),
      );
    });
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final chat = widget.state.chatById(widget.chatId);
    if (chat == null || chat.id.isEmpty) {
      return Scaffold(
        appBar: AppBar(
          title: const AppLogo(text: 'Circles - Chat'),
        ),
        body: const Center(child: Text('Chat no encontrado')),
      );
    }
    return Scaffold(
      appBar: AppBar(
        title: AppLogo(text: 'Circles - ${chat.personName}'),
        bottom: chat.circleObjective != null
            ? PreferredSize(
                preferredSize: const Size.fromHeight(24),
                child: Padding(
                  padding: const EdgeInsets.only(bottom: 8.0),
                  child: Text(
                    chat.circleObjective!,
                    style: Theme.of(context).textTheme.bodySmall,
                  ),
                ),
              )
            : null,
      ),
      body: Column(
        children: [
          Expanded(
            child: _MessageList(
              messages: chat.messages,
              currentIdentity: widget.state.currentIdentity,
            ),
          ),
          _Composer(
            controller: _controller,
            onSend: (text) async {
              final messenger = ScaffoldMessenger.of(context);
              try {
                await widget.state.sendMessage(chat.id, text);
                if (mounted) setState(() {});
              } catch (e) {
                messenger.showSnackBar(
                  SnackBar(content: Text('No pudimos enviar el mensaje: $e')),
                );
              }
            },
          ),
        ],
      ),
    );
  }
}

class _MessageList extends StatelessWidget {
  const _MessageList({
    required this.messages,
    required this.currentIdentity,
  });

  final List<ChatMessage> messages;
  final String currentIdentity;

  @override
  Widget build(BuildContext context) {
    return ListView.separated(
      reverse: true,
      padding: const EdgeInsets.all(16),
      itemCount: messages.length,
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final message = messages[messages.length - 1 - index];
        final isMine = message.senderId == currentIdentity;
        final colorScheme = Theme.of(context).colorScheme;
        final align = isMine
            ? CrossAxisAlignment.end
            : CrossAxisAlignment.start;
        final bg = isMine
            ? colorScheme.secondary.withValues(alpha: 0.18)
            : colorScheme.tertiaryContainer.withValues(alpha: 0.7);
        final textColor = isMine
            ? colorScheme.onSecondaryContainer
            : colorScheme.onTertiaryContainer;
        return Column(
          crossAxisAlignment: align,
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: bg,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(message.text, style: TextStyle(color: textColor)),
            ),
            const SizedBox(height: 4),
            Text(
              _formatTime(message.sentAt),
              style: Theme.of(context).textTheme.bodySmall,
            ),
          ],
        );
      },
    );
  }

  String _formatTime(DateTime dt) {
    final h = dt.hour.toString().padLeft(2, '0');
    final m = dt.minute.toString().padLeft(2, '0');
    return '$h:$m';
  }
}

class _Composer extends StatelessWidget {
  const _Composer({required this.controller, required this.onSend});

  final TextEditingController controller;
  final ValueChanged<String> onSend;

  @override
  Widget build(BuildContext context) {
    return SafeArea(
      child: Padding(
        padding: const EdgeInsets.fromLTRB(12, 8, 12, 12),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: controller,
                decoration: const InputDecoration(
                  hintText: 'Escribe un mensaje...',
                ),
                onSubmitted: (text) => _submit(text),
              ),
            ),
            const SizedBox(width: 8),
            IconButton(
              onPressed: () => _submit(controller.text),
              color: Theme.of(context).colorScheme.secondary,
              icon: const Icon(Icons.send),
            ),
          ],
        ),
      ),
    );
  }

  void _submit(String text) {
    if (text.trim().isEmpty) return;
    onSend(text.trim());
    controller.clear();
  }
}
