package com.example.fitnessapp.utils

fun formatListString(input: String?): String {
    if (input.isNullOrBlank()) return ""
    return input
        .removeSurrounding("[", "]")
        .removeSurrounding("'", "'")
        .split("', '")
        .joinToString("\n• ") { it.trim() }
        .let { if (it.isNotBlank()) "• $it" else "" }
}
