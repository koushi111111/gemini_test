import '../../core/api_client.dart';
import 'chat_models.dart';

/// チャット機能のデータアクセス層。
class ChatRepository {
  ChatRepository({ApiClient? client}) : _client = client ?? ApiClient();

  final ApiClient _client;

  /// バックエンドの疎通確認。
  Future<bool> checkHealth() async {
    try {
      final json = await _client.get('/health');
      return json['status'] == 'ok';
    } on ApiException {
      return false;
    }
  }

  /// Gemini に問い合わせて応答テキストを得る。
  Future<String> sendMessage({
    required String message,
    required List<ChatMessage> history,
  }) async {
    final json = await _client.post('/chat', {
      'message': message,
      'history': history.map((m) => m.toJson()).toList(),
    });
    return json['reply'] as String;
  }
}
