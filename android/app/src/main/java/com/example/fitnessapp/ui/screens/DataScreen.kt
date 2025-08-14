package com.example.fitnessapp.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.fitnessapp.data.Activity
import com.example.fitnessapp.data.ApiService
import com.example.fitnessapp.data.LatestWeight
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext

@Composable
fun DataScreen(userId: Int, onGenerateRecipe: () -> Unit) {
    val api = remember { ApiService.create("https://backend-45111119432.us-central1.run.app/") }
    val latestWeightState = remember { mutableStateOf<LatestWeight?>(null) }
    val activitiesState = remember { mutableStateOf<List<Activity>>(emptyList()) }

    LaunchedEffect(userId) {
        withContext(Dispatchers.IO) {
            try {
                latestWeightState.value = api.getLatestWeight(userId)
                activitiesState.value = api.getActivities(userId)
            } catch (_: Exception) { }
        }
    }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Your Data", style = MaterialTheme.typography.headlineSmall)
        Card(modifier = Modifier.padding(top = 8.dp)) {
            val lw = latestWeightState.value
            val weightText = lw?.let { w ->
                if (w.found && w.weight != null && w.weightUnits != null) "Latest weight: ${w.weight} ${w.weightUnits} on ${w.date}" else "No weight data"
            } ?: "No weight data"
            Text(weightText, modifier = Modifier.padding(16.dp))
        }

        Text("Recent Activities", style = MaterialTheme.typography.titleMedium, modifier = Modifier.padding(top = 16.dp))
        activitiesState.value.take(5).forEach { act ->
            Card(modifier = Modifier.padding(top = 8.dp)) {
                Text("${act.activityDate}: ${act.activityType} - ${act.caloriesBurned ?: 0} cal", modifier = Modifier.padding(12.dp))
            }
        }

        Button(onClick = onGenerateRecipe, modifier = Modifier.padding(top = 24.dp)) {
            Text("Generate Recipe")
        }
    }
}

