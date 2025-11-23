class UserInterest {
  const UserInterest({
    required this.title,
    required this.description,
  });

  final String title;
  final String description;

  factory UserInterest.fromJson(Map<String, dynamic> json) {
    return UserInterest(
      title: (json['title'] ?? json['name'] ?? '').toString(),
      description: (json['description'] ?? json['details'] ?? '').toString(),
    );
  }

  Map<String, dynamic> toJson() => {
        'title': title,
        'description': description,
      };
}

class UserProfile {
  const UserProfile({
    required this.email,
    required this.profileCompleted,
    required this.interests,
    required this.bio,
    this.socialStyle,
    this.boundaries = const [],
    this.availability,
  });

  final String email;
  final bool profileCompleted;
  final List<UserInterest> interests;
  final String bio;
  final String? socialStyle;
  final List<String> boundaries;
  final String? availability;

  factory UserProfile.fromJson(Map<String, dynamic> json) {
    final interestsJson = json['interests'] ?? json['gustos'] ?? [];
    final interestsList = <UserInterest>[];
    if (interestsJson is List) {
      for (final item in interestsJson) {
        if (item is Map<String, dynamic>) {
          interestsList.add(UserInterest.fromJson(item));
        }
      }
    }
    final completedRaw = json['profileCompleted'] ??
        json['profile_completed'] ??
        json['completado'];
    final completed = completedRaw is bool
        ? completedRaw
        : completedRaw.toString().toLowerCase() == 'true';
    final boundariesRaw = json['boundaries'];
    final boundaries = <String>[];
    if (boundariesRaw is List) {
      for (final b in boundariesRaw) {
        if (b != null) boundaries.add(b.toString());
      }
    }
    return UserProfile(
      email: (json['email'] ?? '').toString(),
      profileCompleted: completed,
      interests: interestsList,
      bio: (json['bio'] ?? json['about'] ?? json['descripcion'] ?? '').toString(),
      socialStyle: (json['socialStyle'] ?? '').toString().isNotEmpty
          ? (json['socialStyle'] ?? '').toString()
          : null,
      boundaries: boundaries,
      availability: (json['availability'] ?? '').toString().isNotEmpty
          ? (json['availability'] ?? '').toString()
          : null,
    );
  }

  UserProfile copyWith({
    String? email,
    bool? profileCompleted,
    List<UserInterest>? interests,
    String? bio,
    String? socialStyle,
    List<String>? boundaries,
    String? availability,
  }) {
    return UserProfile(
      email: email ?? this.email,
      profileCompleted: profileCompleted ?? this.profileCompleted,
      interests: interests ?? this.interests,
      bio: bio ?? this.bio,
      socialStyle: socialStyle ?? this.socialStyle,
      boundaries: boundaries ?? this.boundaries,
      availability: availability ?? this.availability,
    );
  }

  Map<String, dynamic> toJson() => {
        'email': email,
        'profileCompleted': profileCompleted,
        'interests': interests.map((i) => i.toJson()).toList(),
        'bio': bio,
        'socialStyle': socialStyle,
        'boundaries': boundaries,
        'availability': availability,
      };
}

class ProfileException implements Exception {
  ProfileException(this.message);
  final String message;

  @override
  String toString() => 'ProfileException: $message';
}
