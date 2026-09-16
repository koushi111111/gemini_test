/// チャット 1 発話ぶんのモデル。バックエンドの ChatMessage と対応する。
class ChatMessage {
  const ChatMessage({required this.role, required this.content});

  /// 'user' または 'model'
  final String role;
  final String content;

  bool get isUser => role == 'user';

  Map<String, dynamic> toJson() => {'role': role, 'content': content};
}
