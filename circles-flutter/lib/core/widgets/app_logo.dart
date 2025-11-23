import 'package:flutter/material.dart';

/// App brand logo replicating the Tailwind markup:
/// - Outer circle (primary) with inner circle (background)
/// - Optional brand text "Circles" with tight tracking
class AppLogo extends StatelessWidget {
  const AppLogo({
    super.key,
    this.size = 32, // 8 (tailwind) -> 32px
    this.gap = 8, // gap-2
    this.showText = true,
    this.text = 'Circles',
    this.textStyle,
    this.primaryColor,
    this.backgroundColor,
  });

  /// Diameter of the outer circle in logical pixels.
  final double size;

  /// Gap between the icon and the text.
  final double gap;

  /// Whether to show the brand text next to the icon.
  final bool showText;

  /// Brand text to render.
  final String text;

  /// Optional text style override.
  final TextStyle? textStyle;

  /// Optional override for the outer circle color (defaults to theme primary).
  final Color? primaryColor;

  /// Optional override for the inner circle color (defaults to theme background).
  final Color? backgroundColor;

  @override
  Widget build(BuildContext context) {
    final ThemeData theme = Theme.of(context);
    final Color resolvedPrimary = primaryColor ?? theme.colorScheme.primary;
    final Color resolvedBackground = backgroundColor ?? theme.colorScheme.surface;

    final Widget icon = Container(
      width: size,
      height: size,
      decoration: BoxDecoration(
        color: resolvedPrimary,
        shape: BoxShape.circle,
      ),
      alignment: Alignment.center,
      child: Container(
        width: size / 2, // 4 (tailwind) -> half of outer
        height: size / 2,
        decoration: BoxDecoration(
          color: resolvedBackground,
          shape: BoxShape.circle,
        ),
      ),
    );

    if (!showText) {
      return icon;
    }

    final TextStyle resolvedTextStyle = (textStyle ??
            theme.textTheme.titleLarge?.copyWith(
              fontWeight: FontWeight.w700, // font-bold
              // tracking-tight (slightly negative letter spacing)
              letterSpacing: -0.2,
              color: theme.colorScheme.onSurface,
            )) ??
        TextStyle(
          fontSize: 20,
          fontWeight: FontWeight.w700,
          letterSpacing: -0.2,
          color: theme.colorScheme.onSurface,
        );

    return Row(
      mainAxisSize: MainAxisSize.min,
      crossAxisAlignment: CrossAxisAlignment.center,
      children: [
        icon,
        SizedBox(width: gap),
        Text(text, style: resolvedTextStyle),
      ],
    );
  }
}

