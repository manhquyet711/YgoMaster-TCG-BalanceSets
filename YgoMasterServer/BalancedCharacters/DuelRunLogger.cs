using System;
using System.Collections.Generic;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace YgoMaster
{
    // Append-only balance evidence. No player names, account codes or tokens.
    sealed class DuelRunLogger
    {
        sealed class Run { public string Id; public bool Ended; public int Chapter; }
        readonly Dictionary<Player, Run> runs = new Dictionary<Player, Run>();
        readonly object sync = new object();
        readonly string file;
        readonly bool test;
        Dictionary<string, object> binaries;
        public DuelRunLogger(string file, bool test) { this.file = file; this.test = test; }

        static string Hash(string path)
        {
            if (!File.Exists(path)) return null;
            using (var stream = File.OpenRead(path))
            using (var sha = SHA256.Create())
                return BitConverter.ToString(sha.ComputeHash(stream)).Replace("-", "").ToLowerInvariant();
        }
        bool Append(Dictionary<string, object> record)
        {
            try {
                record["schemaVersion"] = 1;
                record["timestampUtc"] = DateTime.UtcNow.ToString("o");
                record["test"] = test;
                Directory.CreateDirectory(Path.GetDirectoryName(file));
                File.AppendAllText(file, MiniJSON.Json.Serialize(record) + Environment.NewLine, new UTF8Encoding(false));
                return true;
            } catch (Exception error) { Utils.LogWarning("Balanced run logging failed: " + error.Message); return false; }
        }
        public void Begin(Player player, DuelSettings settings, string playerId, string opponentId,
            string contentVersion, string runtime)
        {
            lock (sync) {
                Run previous;
                runs.TryGetValue(player, out previous);
                if (previous != null && !previous.Ended)
                    previous.Ended = Append(new Dictionary<string, object> {
                        { "event", "end" }, { "runId", previous.Id }, { "result", "interrupted" },
                        { "finishReason", "another_duel_started" }, { "chapterId", previous.Chapter },
                        { "eligibleForWinRate", false } });
                if (playerId == null) { runs.Remove(player); return; }
                var run = new Run { Id = Guid.NewGuid().ToString("N"), Chapter = settings.chapter };
                if (binaries == null) {
                    try {
                        binaries = new Dictionary<string, object> {
                            { "serverSha256", Hash(Path.Combine(runtime, "YgoMaster.exe")) },
                            { "clientSha256", Hash(Path.Combine(runtime, "YgoMasterClient.exe")) },
                            { "gameAssemblySha256", Hash(Path.Combine(Path.GetDirectoryName(runtime), "GameAssembly.dll")) } };
                    } catch (Exception error) { binaries = new Dictionary<string, object> { { "hashError", error.Message } }; }
                }
                Append(new Dictionary<string, object> {
                    { "event", "start" }, { "runId", run.Id }, { "previousRunId", previous == null ? null : previous.Id },
                    { "chapterId", settings.chapter }, { "playerCharacter", playerId }, { "opponentCharacter", opponentId },
                    { "contentVersion", contentVersion }, { "deckRevision", "source-v1" }, { "binaries", binaries },
                    { "deckFingerprints", new [] { CharacterCatalog.ComputeFingerprint(settings.Deck[0]), CharacterCatalog.ComputeFingerprint(settings.Deck[1]) } },
                    { "seed", settings.RandSeed }, { "firstPlayerConfigured", settings.FirstPlayer },
                    { "firstPlayerObserved", null }, { "life", settings.life }, { "hands", settings.hnum },
                    { "cpu", settings.cpu }, { "cpuflag", settings.cpuflag }, { "noshuffle", settings.noshuffle },
                    { "controlMode", "human-vs-cpu" }, { "resultSource", "client_reported" } });
                runs[player] = run;
            }
        }
        public void End(Player player, int chapter, DuelResultType result, DuelFinishType finish, int turns)
        {
            lock (sync) {
                Run run;
                if (!runs.TryGetValue(player, out run) || run.Ended || run.Chapter != chapter) return;
                bool interrupted = finish == DuelFinishType.Failed || finish == DuelFinishType.None ||
                    finish == DuelFinishType.TimeOut || (int)finish >= 100 ||
                    !Enum.IsDefined(typeof(DuelFinishType), finish) ||
                    (result != DuelResultType.Win && result != DuelResultType.Lose && result != DuelResultType.Draw);
                run.Ended = Append(new Dictionary<string, object> {
                    { "event", "end" }, { "runId", run.Id }, { "chapterId", chapter },
                    { "result", interrupted ? "interrupted" : result == DuelResultType.Win ? "win" : result == DuelResultType.Lose ? "loss" : "draw" },
                    { "reportedResult", result.ToString() }, { "finishReason", finish.ToString() },
                    { "turns", turns >= 0 ? (object)turns : null },
                    { "eligibleForWinRate", !interrupted && finish != DuelFinishType.Surrender && result != DuelResultType.Draw } });
            }
        }
    }
}
