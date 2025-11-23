import 'package:flutter/material.dart';

import '../../../core/widgets/app_logo.dart';
import '../../../core/widgets/page_container.dart';
import '../../../core/theme/app_colors.dart';
import '../../../core/theme/card_gradients.dart';
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
  void initState() {
    super.initState();
    widget.state.refreshChats();
  }

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
        title: const AppLogo(text: 'Circles - Chats'),
        actions: [
          IconButton(
            onPressed: widget.onOpenProfile,
            tooltip: 'Perfil',
            icon: const Icon(Icons.person_outline),
          ),
        ],
      ),
      body: PageContainer(
        child: Column(
          children: [
            if (widget.state.error != null) ...[
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: theme.colorScheme.errorContainer,
                  borderRadius: BorderRadius.circular(12),
                ),
                child: Text(
                  widget.state.error!,
                  style: TextStyle(color: theme.colorScheme.onErrorContainer),
                ),
              ),
              const SizedBox(height: 8),
            ],
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                gradient: homeCardGradient(theme.colorScheme),
                border: Border.all(
                  color: theme.colorScheme.primary.withValues(alpha: 0.18),
                ),
                borderRadius: BorderRadius.circular(14),
              ),
              child: TextField(
                controller: _searchController,
                decoration: const InputDecoration(
                  hintText: 'Buscar por nombre u objetivo',
                  prefixIcon: Icon(Icons.search),
                ),
                onChanged: (_) => setState(() {}),
              ),
            ),
            const SizedBox(height: 12),
            Expanded(
              child: hasChats
                  ? _ChatList(state: widget.state, chats: filtered)
                  : _EmptyChats(theme: theme),
            ),
          ],
        ),
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
    final palette = [
      theme.colorScheme.primary,
      theme.colorScheme.secondary,
      theme.colorScheme.tertiary,
      AppColors.accent2,
    ];
    return ListView.separated(
      itemCount: chats.length,
      padding: const EdgeInsets.all(16),
      separatorBuilder: (context, index) => const SizedBox(height: 12),
      itemBuilder: (context, index) {
        final chat = chats[index];
        final accent = palette[index % palette.length];
        return Card(
          child: ListTile(
            leading: CircleAvatar(
              backgroundColor: accent.withValues(alpha: 0.18),
              foregroundColor: accent,
              child: const Icon(Icons.person),
            ),
            title: Text(
              chat.personName,
              style: theme.textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            subtitle: Text(chat.lastMessage ?? ''),
            trailing: chat.unreadCount > 0
                ? Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 6,
                    ),
                    decoration: BoxDecoration(
                      color: theme.colorScheme.secondary,
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Text(
                      chat.unreadCount.toString(),
                      style: TextStyle(color: theme.colorScheme.onSecondary),
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
        builder: (_) => ChatThreadPage(chatId: chat.id, state: state),
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
            Container(
              padding: const EdgeInsets.all(18),
              decoration: BoxDecoration(
                shape: BoxShape.circle,
                color: theme.colorScheme.tertiaryContainer.withValues(
                  alpha: 0.7,
                ),
              ),
              child: Icon(
                Icons.chat_bubble_outline,
                size: 48,
                color: theme.colorScheme.tertiary,
              ),
            ),
            const SizedBox(height: 12),
            Text('No hay chats activos', style: theme.textTheme.titleMedium),
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
