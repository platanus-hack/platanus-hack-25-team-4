import 'package:flutter/material.dart';

import 'app_colors.dart';

final ThemeData appTheme = ThemeData(
  colorScheme: ColorScheme.fromSeed(
    seedColor: AppColors.primary,
    primary: AppColors.primary,
    secondary: AppColors.secondary,
    surface: AppColors.bgLight,
    brightness: Brightness.light,
  ),
  scaffoldBackgroundColor: AppColors.bgLight,
  useMaterial3: true,
  textTheme: Typography.blackMountainView.apply(
    bodyColor: AppColors.textPrimary,
    displayColor: AppColors.textPrimary,
  ),
  inputDecorationTheme: const InputDecorationTheme(
    filled: true,
    fillColor: Colors.white,
    border: OutlineInputBorder(
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
    focusedBorder: OutlineInputBorder(
      borderSide: BorderSide(color: AppColors.primary, width: 1.5),
      borderRadius: BorderRadius.all(Radius.circular(12)),
    ),
    contentPadding: EdgeInsets.symmetric(horizontal: 14, vertical: 14),
  ),
  cardTheme: const CardThemeData(
    color: Colors.white,
    elevation: 3,
    shape: RoundedRectangleBorder(
      borderRadius: BorderRadius.all(Radius.circular(16)),
    ),
  ),
  filledButtonTheme: FilledButtonThemeData(
    style: FilledButton.styleFrom(
      backgroundColor: AppColors.primary,
      foregroundColor: Colors.white,
      padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      textStyle: const TextStyle(fontWeight: FontWeight.w600),
    ),
  ),
);
