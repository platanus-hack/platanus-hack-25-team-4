import 'package:flutter/material.dart';

import 'app_colors.dart';

final ThemeData appTheme = ThemeData(
  colorScheme:
      ColorScheme.fromSeed(
        seedColor: AppColors.primary,
        primary: AppColors.primary,
        secondary: AppColors.secondary,
        tertiary: AppColors.accent1,
        surface: Colors.white,
        background: AppColors.bgLight,
        brightness: Brightness.light,
      ).copyWith(
        surfaceContainerHigh: Colors.white,
        surfaceContainerLow: AppColors.bgLight,
        primaryContainer: AppColors.primary.withOpacity(0.12),
        secondaryContainer: AppColors.secondary.withOpacity(0.12),
        tertiaryContainer: AppColors.accent1.withOpacity(0.12),
        outlineVariant: AppColors.textSecondary.withOpacity(0.2),
      ),
  scaffoldBackgroundColor: AppColors.bgLight,
  useMaterial3: true,
  textTheme: Typography.blackMountainView.apply(
    bodyColor: AppColors.textPrimary,
    displayColor: AppColors.textPrimary,
  ),
  appBarTheme: const AppBarTheme(
    backgroundColor: Colors.white,
    foregroundColor: AppColors.textPrimary,
    elevation: 1,
    shadowColor: Colors.black12,
    surfaceTintColor: Colors.transparent,
  ),
  inputDecorationTheme: InputDecorationTheme(
    filled: true,
    fillColor: Colors.white,
    prefixIconColor: AppColors.textSecondary,
    border: const OutlineInputBorder(
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
    focusedBorder: const OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.primary, width: 1.5),
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
  ),
  cardTheme: CardThemeData(
    color: Colors.white,
    elevation: 4,
    margin: EdgeInsets.zero,
    shadowColor: AppColors.textSecondary.withOpacity(0.08),
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(16)),
    ),
  ),
  floatingActionButtonTheme: const FloatingActionButtonThemeData(
    backgroundColor: AppColors.accent1,
    foregroundColor: AppColors.textPrimary,
  ),
  navigationBarTheme: NavigationBarThemeData(
    backgroundColor: Colors.white,
    elevation: 2,
    indicatorColor: AppColors.secondary.withOpacity(0.16),
    surfaceTintColor: Colors.transparent,
    labelTextStyle: MaterialStateProperty.all(
      const TextStyle(fontWeight: FontWeight.w600),
    ),
  ),
  navigationRailTheme: NavigationRailThemeData(
    backgroundColor: AppColors.bgLight,
    indicatorColor: AppColors.secondary.withOpacity(0.18),
    selectedIconTheme: const IconThemeData(color: AppColors.secondary),
    selectedLabelTextStyle: const TextStyle(
      color: AppColors.secondary,
      fontWeight: FontWeight.w700,
    ),
  ),
  chipTheme: ChipThemeData(
    backgroundColor: AppColors.accent2.withOpacity(0.18),
    selectedColor: AppColors.secondary.withOpacity(0.18),
    labelStyle: const TextStyle(color: AppColors.textPrimary),
    secondaryLabelStyle: const TextStyle(color: AppColors.textPrimary),
    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
  ),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      backgroundColor: AppColors.primary,
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      textStyle: const TextStyle(fontWeight: FontWeight.w600),
    ),
  ),
  outlinedButtonTheme: OutlinedButtonThemeData(
    style: OutlinedButton.styleFrom(
      foregroundColor: AppColors.secondary,
      side: const BorderSide(color: AppColors.secondary),
      textStyle: const TextStyle(fontWeight: FontWeight.w600),
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
    ),
  ),
  textButtonTheme: TextButtonThemeData(
    style: TextButton.styleFrom(
      foregroundColor: AppColors.secondary,
      textStyle: const TextStyle(fontWeight: FontWeight.w600),
    ),
  ),
);