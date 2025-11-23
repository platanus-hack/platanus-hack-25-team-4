import 'package:flutter/material.dart';

import 'app_colors.dart';

const double _fieldRadius = 12;
const double _cardRadius = 16;

final ColorScheme _colorScheme = ColorScheme.light(
  primary: AppColors.primary,
  onPrimary: AppColors.bgLight,
  primaryContainer: AppColors.primary.withValues(alpha: 0.14),
  onPrimaryContainer: AppColors.bgDark,
  secondary: AppColors.secondary,
  onSecondary: AppColors.bgDark,
  secondaryContainer: AppColors.secondary.withValues(alpha: 0.16),
  onSecondaryContainer: AppColors.bgDark,
  tertiary: AppColors.accent1,
  onTertiary: AppColors.bgDark,
  tertiaryContainer: AppColors.accent1.withValues(alpha: 0.18),
  onTertiaryContainer: AppColors.bgDark,
  surface: AppColors.bgLight,
  onSurface: AppColors.textPrimary,
  error: AppColors.secondary,
  onError: AppColors.bgDark,
  errorContainer: AppColors.accent2.withValues(alpha: 0.4),
  onErrorContainer: AppColors.bgDark,
  outline: AppColors.textSecondary.withValues(alpha: 0.45),
  outlineVariant: AppColors.textSecondary.withValues(alpha: 0.25),
  shadow: AppColors.bgDark.withValues(alpha: 0.18),
  scrim: AppColors.bgDark.withValues(alpha: 0.32),
  inverseSurface: AppColors.bgDark,
  onInverseSurface: AppColors.bgLight,
  inversePrimary: AppColors.secondary,
  surfaceTint: AppColors.primary,
).copyWith(
  surfaceContainerHighest: AppColors.bgLight,
  surfaceContainerHigh: AppColors.bgLight,
  surfaceContainer: AppColors.bgLight,
  surfaceContainerLow: AppColors.bgLight,
  surfaceContainerLowest: AppColors.bgLight,
);

final ThemeData appTheme = ThemeData(
  colorScheme: _colorScheme,
  scaffoldBackgroundColor: AppColors.bgLight,
  useMaterial3: true,
  textTheme: Typography.blackMountainView.apply(
    bodyColor: AppColors.textPrimary,
    displayColor: AppColors.textPrimary,
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: Colors.white,
    foregroundColor: AppColors.textPrimary,
    elevation: 0,
    surfaceTintColor: Colors.transparent,
    iconTheme: IconThemeData(color: AppColors.textPrimary),
    titleTextStyle: TextStyle(
      color: AppColors.textPrimary,
      fontSize: 20,
      fontWeight: FontWeight.w700,
    ),
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: _colorScheme.surface,
    prefixIconColor: AppColors.textSecondary,
    suffixIconColor: AppColors.textSecondary,
    labelStyle: const TextStyle(color: AppColors.textSecondary),
    hintStyle: TextStyle(
      color: AppColors.textSecondary.withValues(alpha: 0.7),
    ),
    border: const OutlineInputBorder(
      borderRadius: BorderRadius.all(Radius.circular(_fieldRadius)),
    ),
    enabledBorder: OutlineInputBorder(
      borderSide: BorderSide(color: _colorScheme.outlineVariant),
      borderRadius: const BorderRadius.all(Radius.circular(_fieldRadius)),
    ),
    focusedBorder: const OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.primary, width: 1.6),
      borderRadius: BorderRadius.all(Radius.circular(_fieldRadius)),
    ),
    errorBorder: const OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.secondary, width: 1.2),
      borderRadius: BorderRadius.all(Radius.circular(_fieldRadius)),
    ),
    focusedErrorBorder: const OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.secondary, width: 1.4),
      borderRadius: BorderRadius.all(Radius.circular(_fieldRadius)),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
  ),
  cardTheme: CardThemeData(
    color: _colorScheme.surfaceContainerHigh,
    elevation: 6,
    margin: EdgeInsets.zero,
    shadowColor: AppColors.bgDark.withValues(alpha: 0.16),
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(_cardRadius)),
    ),
  ),
  floatingActionButtonTheme: FloatingActionButtonThemeData(
    backgroundColor: AppColors.accent1,
    foregroundColor: AppColors.bgDark,
    elevation: 3,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.circular(16),
    ),
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: Colors.white,
    elevation: 4,
    indicatorColor: _colorScheme.secondaryContainer,
    surfaceTintColor: Colors.transparent,
    iconTheme: WidgetStateProperty.all(
      const IconThemeData(color: AppColors.textSecondary),
    ),
    labelTextStyle: WidgetStateProperty.all(
      const TextStyle(
        color: AppColors.textPrimary,
        fontWeight: FontWeight.w600,
      ),
    ),
  ),
  navigationRailTheme: NavigationRailThemeData(
    backgroundColor: Colors.white,
    indicatorColor: _colorScheme.secondaryContainer,
    selectedIconTheme: const IconThemeData(color: AppColors.textPrimary),
    unselectedIconTheme: const IconThemeData(color: AppColors.textSecondary),
    selectedLabelTextStyle: const TextStyle(
      color: AppColors.textPrimary,
      fontWeight: FontWeight.w700,
    ),
    unselectedLabelTextStyle: const TextStyle(
      color: AppColors.textSecondary,
    ),
  ),
  chipTheme: ChipThemeData(
    backgroundColor: _colorScheme.tertiaryContainer,
    selectedColor: _colorScheme.secondaryContainer,
    labelStyle: const TextStyle(color: AppColors.textPrimary),
    secondaryLabelStyle: const TextStyle(color: AppColors.textPrimary),
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
  ),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      backgroundColor: _colorScheme.primary,
      foregroundColor: _colorScheme.onPrimary,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(_fieldRadius),
      ),
      textStyle: const TextStyle(fontWeight: FontWeight.w700),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: _colorScheme.secondary,
      side: BorderSide(color: _colorScheme.secondary),
      textStyle: const TextStyle(fontWeight: FontWeight.w700),
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 18),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(_fieldRadius),
      ),
    ),
  ),
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: _colorScheme.secondary,
      textStyle: const TextStyle(fontWeight: FontWeight.w700),
    ),
  ),
  dividerTheme: DividerThemeData(
    color: _colorScheme.outlineVariant,
    thickness: 1,
  ),
);
