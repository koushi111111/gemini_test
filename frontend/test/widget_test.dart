import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:tx_hackathon_gc/features/chat/chat_models.dart';
import 'package:tx_hackathon_gc/features/chat/chat_repository.dart';
import 'package:tx_hackathon_gc/features/chat/chat_screen.dart';

/// バックエンドを呼ばないテスト用リポジトリ。
class FakeChatRepository implements ChatRepository {
  @override
  Future<bool> checkHealth() async => true;

  @override
  Future<String> sendMessage({
    required String message,
    required List<ChatMessage> history,
  }) async => 'echo: $message';
}

void main() {
  testWidgets('メッセージを送信すると応答が表示される', (tester) async {
    await tester.pumpWidget(
      MaterialApp(home: ChatScreen(repository: FakeChatRepository())),
    );

    expect(find.text('メッセージを送信してください'), findsOneWidget);

    await tester.enterText(find.byType(TextField), 'こんにちは');
    await tester.tap(find.byIcon(Icons.send));
    await tester.pumpAndSettle();

    expect(find.text('こんにちは'), findsOneWidget);
    expect(find.text('echo: こんにちは'), findsOneWidget);
  });
}
