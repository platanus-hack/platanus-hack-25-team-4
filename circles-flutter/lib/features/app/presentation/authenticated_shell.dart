import 'package:flutter/material.dart';

import '../../../core/theme/app_colors.dart';
import '../../app/app_state.dart';
import '../../auth/domain/auth_session.dart';
import '../../chats/presentation/chats_page.dart';
import '../../circles/presentation/circles_page.dart';
import '../../home/presentation/home_dashboard_page.dart';
import '../../matches/presentation/matches_page.dart';
import '../../profile/presentation/profile_page.dart';

class AuthenticatedShell extends StatefulWidget {
  const AuthenticatedShell({
    super.key,
    required this.session,
    required this.onLogout,
  });

  final AuthSession session;
  final VoidCallback onLogout;

  @override
  State<AuthenticatedShell> createState() => _AuthenticatedShellState();
}

class _AuthenticatedShellState extends State<AuthenticatedShell> {
  int _index = 0;
  late final AppState _state;

  @override
  void initState() {
    super.initState();
    _state = AppState(session: widget.session);
    _state.addListener(_onStateChanged);
    _state.initialize();
  }

  @override
  void dispose() {
    _state.removeListener(_onStateChanged);
    _state.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.of(context).size.width >= 900;
    final pages = [
      HomeDashboardPage(
        onNavigateToCircles: () => _onSelect(1),
        onNavigateToMatches: () => _onSelect(2),
        state: _state,
        onOpenProfile: _openProfile,
      ),
      CirclesPage(
        state: _state,
        onOpenProfile: _openProfile,
      ),
      MatchesPage(
        state: _state,
        onOpenProfile: _openProfile,
      ),
      ChatsPage(
        state: _state,
        onOpenProfile: _openProfile,
      ),
    ];
    return Scaffold(
      body: Row(
        children: [
          if (isWide) _NavRail(index: _index, onSelect: _onSelect),
          Expanded(
            child: IndexedStack(
              index: _index,
              children: pages,
            ),
          ),
        ],
      ),
      bottomNavigationBar: isWide
          ? null
          : NavigationBar(
              selectedIndex: _index,
              onDestinationSelected: _onSelect,
              destinations: const [
                NavigationDestination(
                  icon: Icon(Icons.home_outlined),
                  selectedIcon: Icon(Icons.home),
                  label: 'Inicio',
                ),
                NavigationDestination(
                  icon: Icon(Icons.hub_outlined),
                  selectedIcon: Icon(Icons.hub),
                  label: 'Círculos',
                ),
                NavigationDestination(
                  icon: Icon(Icons.people_outline),
                  selectedIcon: Icon(Icons.people),
                  label: 'Matches',
                ),
                NavigationDestination(
                  icon: Icon(Icons.chat_bubble_outline),
                  selectedIcon: Icon(Icons.chat_bubble),
                  label: 'Chats',
                ),
              ],
            ),
    );
  }

  void _onSelect(int value) {
    if (_index == value) return;
    setState(() => _index = value);
  }

  void _onStateChanged() {
    setState(() {});
  }

  void _openProfile() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProfilePage(
          session: widget.session,
          onLogout: widget.onLogout,
        ),
      ),
    );
  }
}

class _NavRail extends StatelessWidget {
  const _NavRail({required this.index, required this.onSelect});

  final int index;
  final ValueChanged<int> onSelect;

  @override
  Widget build(BuildContext context) {
    return NavigationRail(
      selectedIndex: index,
      onDestinationSelected: onSelect,
      labelType: NavigationRailLabelType.all,
      backgroundColor: AppColors.bgLight,
      destinations: const [
        NavigationRailDestination(
          icon: Icon(Icons.home_outlined),
          selectedIcon: Icon(Icons.home),
          label: Text('Inicio'),
        ),
        NavigationRailDestination(
          icon: Icon(Icons.hub_outlined),
          selectedIcon: Icon(Icons.hub),
          label: Text('Círculos'),
        ),
        NavigationRailDestination(
          icon: Icon(Icons.people_outline),
          selectedIcon: Icon(Icons.people),
          label: Text('Matches'),
        ),
        NavigationRailDestination(
          icon: Icon(Icons.chat_bubble_outline),
          selectedIcon: Icon(Icons.chat_bubble),
          label: Text('Chats'),
        ),
      ],
    );
  }
}
