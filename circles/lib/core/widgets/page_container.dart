import 'package:flutter/material.dart';

/// Centers page content and adds responsive horizontal padding so views
/// stay readable on wide screens without feeling cramped on mobile.
class PageContainer extends StatelessWidget {
  const PageContainer({super.key, required this.child});

  final Widget child;

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        final horizontalPadding = constraints.maxWidth >= 1200
            ? 48.0
            : constraints.maxWidth >= 900
                ? 32.0
                : 16.0;
        return Center(
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 1100),
            child: Padding(
              padding: EdgeInsets.fromLTRB(
                horizontalPadding,
                16,
                horizontalPadding,
                16,
              ),
              child: child,
            ),
          ),
        );
      },
    );
  }
}
