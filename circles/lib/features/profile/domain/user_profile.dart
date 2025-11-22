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
  });

  final String email;
  final bool profileCompleted;
  final List<UserInterest> interests;
  final String bio;

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
    return UserProfile(
      email: (json['email'] ?? '').toString(),
      profileCompleted: completed,
      interests: interestsList,
      bio: (json['bio'] ?? json['about'] ?? json['descripcion'] ?? '').toString(),
    );
  }

  UserProfile copyWith({
    String? email,
    bool? profileCompleted,
    List<UserInterest>? interests,
    String? bio,
  }) {
    return UserProfile(
      email: email ?? this.email,
      profileCompleted: profileCompleted ?? this.profileCompleted,
      interests: interests ?? this.interests,
      bio: bio ?? this.bio,
    );
  }

  Map<String, dynamic> toJson() => {
        'email': email,
        'profileCompleted': profileCompleted,
        'interests': interests.map((i) => i.toJson()).toList(),
        'bio': bio,
      };
}

class ProfileException implements Exception {
  ProfileException(this.message);
  final String message;

  @override
  String toString() => 'ProfileException: $message';
}
