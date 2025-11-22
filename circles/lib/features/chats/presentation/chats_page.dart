import 'package:flutter/material.dart';

import '../../app/app_state.dart';
import '../domain/chat_thread.dart';
import 'chat_thread_page.dart';

class ChatsPage extends StatefulWidget {
  const ChatsPage({
    super.key,
    required this.state,
    required this.onOpenProfile,
  });

  final AppState state;
  final VoidCallback onOpenProfile;

  @override
  State<ChatsPage> createState() => _ChatsPageState();
}

class _ChatsPageState extends State<ChatsPage> {
  final TextEditingController _searchController = TextEditingController();

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final filtered = _filtered();
    final hasChats = filtered.isNotEmpty;
    return Scaffold(
      appBar: AppBar(
        title: const Text('Chats'),
        actions: [
          IconButton(
            onPressed: widget.onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(16),
            child: TextField(
              controller: _searchController,
              decoration: const InputDecoration(
                hintText: 'Buscar por nombre u objetivo',
                prefixIcon: Icon(Icons.search),
              ),
              onChanged: (_) => setState(() {}),
            ),
          ),
          Expanded(
            child: hasChats
                ? _ChatList(state: widget.state, chats: filtered)
                : _EmptyChats(theme: theme),
          ),
        ],
      ),
    );
  }

  List<ChatThread> _filtered() {
    final query = _searchController.text.trim().toLowerCase();
    if (query.isEmpty) return widget.state.chats;
    return widget.state.chats.where((c) {
      return c.personName.toLowerCase().contains(query) ||
          (c.circleObjective?.toLowerCase().contains(query) ?? false);
    }).toList();
  }
}

class _ChatList extends StatelessWidget {
  const _ChatList({required this.state, required this.chats});

  final AppState state;
  final List<ChatThread> chats;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return ListView.separated(
      itemCount: chats.length,
      padding: const EdgeInsets.all(16),
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final chat = chats[index];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor:
                  theme.colorScheme.primary.withValues(alpha: 0.1),
              foregroundColor: theme.colorScheme.primary,
              child: const Icon(Icons.person),
            ),
            title: Text(
              chat.personName,
              style: theme.textTheme.titleMedium
                  ?.copyWith(fontWeight: FontWeight.w600),
            ),
            subtitle: Text(chat.lastMessage ?? ''),
            trailing: chat.unreadCount > 0
                ? Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.primary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      chat.unreadCount.toString(),
                      style: const TextStyle(color: Colors.white),
                    ),
                  )
                : null,
            onTap: () => _openThread(context, chat),
          ),
        );
      },
    );
  }

  void _openThread(BuildContext context, ChatThread chat) {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ChatThreadPage(
          chatId: chat.id,
          state: state,
        ),
      ),
    );
  }
}

class _EmptyChats extends StatelessWidget {
  const _EmptyChats({required this.theme});

  final ThemeData theme;

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.chat_bubble_outline,
                size: 64, color: theme.colorScheme.primary),
            const SizedBox(height: 12),
            Text(
              'No hay chats activos',
              style: theme.textTheme.titleMedium,
            ),
            const SizedBox(height: 8),
            Text(
              'Acepta un match para habilitar el chat con esa persona.',
              textAlign: TextAlign.center,
              style: theme.textTheme.bodyMedium,
            ),
          ],
        ),
      ),
    );
  }
}
