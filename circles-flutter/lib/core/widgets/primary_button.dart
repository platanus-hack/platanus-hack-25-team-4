import 'package:flutter/material.dart';

import '../theme/app_colors.dart';

class PrimaryButton extends StatelessWidget {
  const PrimaryButton({
    super.key,
    required this.label,
    this.loadingLabel,
    this.icon,
    this.onPressed,
    this.loading = false,
    this.backgroundColor,
    this.foregroundColor,
  });

  final String label;
  final String? loadingLabel;
  final IconData? icon;
  final VoidCallback? onPressed;
  final bool loading;
  final Color? backgroundColor;
  final Color? foregroundColor;

  @override
  Widget build(BuildContext context) {
    final text = loading ? (loadingLabel ?? label) : label;
    final colorScheme = Theme.of(context).colorScheme;
    final background = backgroundColor ?? colorScheme.primary;
    final resolvedForeground =
        foregroundColor ??
        (backgroundColor == null
            ? colorScheme.onPrimary
            : ThemeData.estimateBrightnessForColor(background) ==
                  Brightness.dark
            ? Colors.white
            : AppColors.textPrimary);
    return FilledButton(
      style: FilledButton.styleFrom(
        backgroundColor: backgroundColor,
        foregroundColor: resolvedForeground,
        padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 20),
        minimumSize: const Size.fromHeight(52),
        textStyle: const TextStyle(fontWeight: FontWeight.w600, inherit: true),
      ),
      onPressed: loading ? null : onPressed,
      child: Row(
        mainAxisSize: MainAxisSize.min,
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (loading)
            const SizedBox(
              width: 16,
              height: 16,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: Colors.white,
              ),
            )
          else if (icon != null)
            Icon(icon, size: 20),
          if (loading || icon != null) const SizedBox(width: 8),
          Text(text),
        ],
      ),
    );
  }
}
