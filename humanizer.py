#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import random
import statistics
from typing import Optional, List

def get_sentences(text: str) -> List[str]:
    parts = re.split(r'(?<=[.!?…])\s+', text.strip())
    return [s.strip() for s in parts if s.strip()]

def sentence_lengths(sents: List[str]) -> List[int]:
    return [len(s.split()) for s in sents]

def burstiness(sents: List[str]) -> float:
    lengths = sentence_lengths(sents)
    if len(lengths) < 2:
        return 0.0
    return statistics.stdev(lengths)

def split_long_sentence(sent: str, rng: random.Random, min_words: int = 12) -> List[str]:
    words = sent.split()
    if len(words) < min_words:
        return [sent]

    candidates = []
    for i, w in enumerate(words[:-3]):
        clean = re.sub(r'[^\wа-яёА-ЯЁ]', '', w.lower())
        if w.endswith(',') or clean in {
            'и', 'а', 'но', 'что', 'когда', 'если', 'потому', 'однако',
            'чтобы', 'который', 'которая', 'которое', 'которые', 'также',
            'кроме', 'того', 'при', 'этом'
        }:
            candidates.append(i + 1)

    if not candidates:
        mid = len(words) // 2
        candidates = [mid]

    cut = rng.choice(candidates)
    left = ' '.join(words[:cut]).rstrip(',;')
    right = ' '.join(words[cut:])
    if right:
        right = right[0].upper() + right[1:]
    return [left + '.', right]

def merge_short_sentences(s1: str, s2: str, rng: random.Random) -> str:
    s1 = s1.rstrip('.!?…')
    connector = rng.choice([', а ', ', и ', ' — ', ', при этом ', '. '])
    if connector == '. ':
        return s1 + '. ' + s2
    return s1 + connector + s2[0].lower() + s2[1:]

def humanize_statistical(
    text: str,
    entropy: Optional[str] = None,
    target_burstiness: float = 8.0,
    max_passes: int = 12,
    intensity: float = 0.85
) -> str:
    if not text.strip():
        return text

    seed = hash(entropy) if entropy else random.randint(0, 10**12)
    rng = random.Random(seed)

    sents = get_sentences(text)
    if len(sents) < 2:
        return text

    for _ in range(max_passes):
        current_burst = burstiness(sents)
        if current_burst >= target_burstiness:
            break

        lengths = sentence_lengths(sents)
        new_sents = []
        i = 0

        while i < len(sents):
            sent = sents[i]
            length = lengths[i]

            # Агрессивное разрезание длинных предложений
            if length >= 13 and rng.random() < intensity * 0.7:
                parts = split_long_sentence(sent, rng, min_words=12)
                new_sents.extend(parts)
                i += 1
                continue

            # Склеивание коротких
            if (i < len(sents) - 1 and 
                length <= 12 and lengths[i+1] <= 13 and 
                rng.random() < intensity * 0.6):
                merged = merge_short_sentences(sent, sents[i+1], rng)
                new_sents.append(merged)
                i += 2
                continue

            # Создание коротких фрагментов
            if length >= 16 and rng.random() < intensity * 0.35:
                words = sent.split()
                cut = rng.randint(4, min(8, len(words)-4))
                left = ' '.join(words[:cut]).rstrip(',;') + '.'
                right = ' '.join(words[cut:])
                if right:
                    right = right[0].upper() + right[1:]
                new_sents.append(left)
                new_sents.append(right)
                i += 1
                continue

            # Swap по запятой
            if ',' in sent and length > 10 and rng.random() < intensity * 0.3:
                parts = [p.strip() for p in sent.split(',', 1)]
                if len(parts) == 2 and len(parts[0].split()) >= 4:
                    new_sent = parts[1].capitalize() + ', ' + parts[0].lower()
                    if not new_sent.endswith(('.', '!', '?')):
                        new_sent += '.'
                    new_sents.append(new_sent)
                    i += 1
                    continue

            new_sents.append(sent)
            i += 1

        sents = [s for s in new_sents if s.strip()]

        # Принудительный разрез самого длинного предложения
        if burstiness(sents) < target_burstiness and len(sents) > 0:
            lengths = sentence_lengths(sents)
            max_idx = lengths.index(max(lengths))
            if lengths[max_idx] >= 14:
                parts = split_long_sentence(sents[max_idx], rng, min_words=10)
                sents = sents[:max_idx] + parts + sents[max_idx+1:]

    # Финальный шум пунктуации
    result = []
    for sent in sents:
        if rng.random() < 0.15 and sent.endswith('.'):
            sent = sent[:-1] + rng.choice(['.', '...', '.'])
        result.append(sent)

    return ' '.join(result)

def analyze_text(text: str, label: str = ""):
    sents = get_sentences(text)
    lengths = sentence_lengths(sents)

    if len(lengths) < 2:
        print(f"{label}: слишком мало предложений для статистики")
        return

    mean_len = statistics.mean(lengths)
    std_len = statistics.stdev(lengths)
    cv = std_len / mean_len if mean_len else 0

    print(f"\n=== {label} ===")
    print(f"Предложений     : {len(sents)}")
    print(f"Средняя длина   : {mean_len:.1f} слов")
    print(f"Burstiness (std): {std_len:.2f}")
    print(f"Коэф. вариации  : {cv:.2f}")
    print(f"Мин / Макс      : {min(lengths)} / {max(lengths)}")

def main():
    print("=" * 60)
    print("  Статистический хуманизатор текста (без словарей)")
    print("=" * 60)
    print("Вставь текст, который нужно обработать.")
    print("Чтобы закончить ввод — нажми Enter на пустой строке.\n")

    lines = []
    while True:
        try:
            line = input()
            if line.strip() == "" and lines:
                break
            lines.append(line)
        except EOFError:
            break

    original = "\n".join(lines).strip()

    if not original:
        print("Текст не введён. Выход.")
        return

    print("\n" + "-" * 60)
    entropy = input("Энтропия / соль (можно оставить пустым): ").strip()
    if not entropy:
        entropy = None

    try:
        intensity_input = input("Интенсивность (0.3–1.0, Enter = 0.85): ").strip()
        intensity = float(intensity_input) if intensity_input else 0.85
        intensity = max(0.3, min(1.0, intensity))
    except ValueError:
        intensity = 0.85

    print("\nОбрабатываю...")

    humanized = humanize_statistical(
        original,
        entropy=entropy,
        target_burstiness=8.0,
        intensity=intensity
    )

    print("\n" + "=" * 60)
    print("РЕЗУЛЬТАТ:")
    print("=" * 60)
    print(humanized)
    print("=" * 60)

    analyze_text(original, "ДО")
    analyze_text(humanized, "ПОСЛЕ")

    print("\nГотово.")

if __name__ == "__main__":
    main()
