package com.example.fitnessapp.ui.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

private val YellowPrimary = Color(0xFFFFC107)
private val YellowOnPrimary = Color(0xFF000000)
private val YellowSecondary = Color(0xFFFFE082)
private val YellowBackground = Color(0xFFFFF8E1)
private val YellowSurface = Color(0xFFFFF3CD)

private val LightColors = lightColorScheme(
    primary = YellowPrimary,
    onPrimary = YellowOnPrimary,
    secondary = YellowSecondary,
    background = YellowBackground,
    surface = YellowSurface
)

@Composable
fun FitnessTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = LightColors,
        typography = Typography,
        content = content
    )
}

