package com.example.fitnessapp.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateListOf
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.rememberCoroutineScope
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.example.fitnessapp.data.ApiService
import com.example.fitnessapp.data.Biometrics
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext
import java.time.LocalDate
import java.time.format.DateTimeFormatter

@Composable
fun BiometricsScreen(userId: Int, onBack: () -> Unit) {
    val api = remember { ApiService.create("https://backend-45111119432.us-central1.run.app/") }
    val scope = rememberCoroutineScope()

    val biometrics = remember { mutableStateListOf<Biometrics>() }
    val loading = remember { mutableStateOf(false) }
    val error = remember { mutableStateOf<String?>(null) }
    val showAddForm = remember { mutableStateOf(false) }

    // Form state for adding new biometric entry
    val weight = remember { mutableStateOf("") }
    val weightUnits = remember { mutableStateOf("lbs") }
    val avgHr = remember { mutableStateOf("") }
    val highHr = remember { mutableStateOf("") }
    val lowHr = remember { mutableStateOf("") }
    val notes = remember { mutableStateOf("") }

    fun fetchBiometrics() {
        scope.launch {
            loading.value = true
            error.value = null
            try {
                val list = withContext(Dispatchers.IO) {
                    api.getBiometrics(userId)
                }
                biometrics.clear()
                biometrics.addAll(list.sortedByDescending { it.date })
            } catch (e: Exception) {
                error.value = "Failed to load biometrics: ${e.message}"
            } finally {
                loading.value = false
            }
        }
    }

    fun addBiometric() {
        if (weight.value.isBlank()) {
            error.value = "Weight is required"
            return
        }

        scope.launch {
            try {
                val today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd"))
                val newBiometric = Biometrics(
                    biometricId = null,
                    userId = userId,
                    date = today,
                    weight = weight.value.toDoubleOrNull(),
                    weightUnits = weightUnits.value,
                    avgHr = avgHr.value.toIntOrNull(),
                    highHr = highHr.value.toIntOrNull(),
                    lowHr = lowHr.value.toIntOrNull(),
                    notes = notes.value.ifBlank { null }
                )

                withContext(Dispatchers.IO) {
                    api.createBiometric(newBiometric)
                }

                // Reset form
                weight.value = ""
                avgHr.value = ""
                highHr.value = ""
                lowHr.value = ""
                notes.value = ""
                showAddForm.value = false

                // Refresh data
                fetchBiometrics()
            } catch (e: Exception) {
                error.value = "Failed to add biometric: ${e.message}"
            }
        }
    }

    LaunchedEffect(userId) { fetchBiometrics() }

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween, verticalAlignment = Alignment.CenterVertically) {
            Text("Biometrics", style = MaterialTheme.typography.headlineSmall)
            Button(onClick = onBack) { Text("Back") }
        }

        if (error.value != null) {
            Text(error.value!!, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp))
        }

        Row(modifier = Modifier.fillMaxWidth().padding(top = 16.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            Button(
                onClick = { showAddForm.value = !showAddForm.value },
                modifier = Modifier.weight(1f)
            ) {
                Text(if (showAddForm.value) "Cancel" else "Add Entry")
            }
            Button(
                onClick = { fetchBiometrics() },
                modifier = Modifier.weight(1f)
            ) {
                Text("Refresh")
            }
        }

        if (showAddForm.value) {
            Card(modifier = Modifier.fillMaxWidth().padding(top = 16.dp)) {
                Column(modifier = Modifier.padding(16.dp)) {
                    Text("Add New Entry", style = MaterialTheme.typography.titleMedium)
                    
                    Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = weight.value,
                            onValueChange = { weight.value = it },
                            label = { Text("Weight") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = weightUnits.value,
                            onValueChange = { weightUnits.value = it },
                            label = { Text("Units") },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                        OutlinedTextField(
                            value = avgHr.value,
                            onValueChange = { avgHr.value = it },
                            label = { Text("Avg HR") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = highHr.value,
                            onValueChange = { highHr.value = it },
                            label = { Text("High HR") },
                            modifier = Modifier.weight(1f)
                        )
                        OutlinedTextField(
                            value = lowHr.value,
                            onValueChange = { lowHr.value = it },
                            label = { Text("Low HR") },
                            modifier = Modifier.weight(1f)
                        )
                    }

                    OutlinedTextField(
                        value = notes.value,
                        onValueChange = { notes.value = it },
                        label = { Text("Notes") },
                        modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                    )

                    Button(
                        onClick = { addBiometric() },
                        modifier = Modifier.fillMaxWidth().padding(top = 8.dp)
                    ) {
                        Text("Save Entry")
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        // Summary cards
        if (biometrics.isNotEmpty()) {
            val latest = biometrics.first()
            val weightTrend = if (biometrics.size >= 2) {
                val current = biometrics[0].weight ?: 0.0
                val previous = biometrics[1].weight ?: 0.0
                current - previous
            } else 0.0

            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.primaryContainer)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Current Weight", style = MaterialTheme.typography.bodySmall)
                        Text(
                            "${latest.weight ?: "N/A"} ${latest.weightUnits ?: ""}",
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold
                        )
                    }
                }
                Card(
                    modifier = Modifier.weight(1f),
                    colors = CardDefaults.cardColors(containerColor = MaterialTheme.colorScheme.secondaryContainer)
                ) {
                    Column(modifier = Modifier.padding(12.dp)) {
                        Text("Trend", style = MaterialTheme.typography.bodySmall)
                        Text(
                            if (weightTrend > 0) "+${String.format("%.1f", weightTrend)}" else String.format("%.1f", weightTrend),
                            style = MaterialTheme.typography.titleMedium,
                            fontWeight = FontWeight.Bold,
                            color = if (weightTrend < 0) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.error
                        )
                    }
                }
            }
        }

        Spacer(Modifier.height(16.dp))

        if (loading.value) {
            Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                CircularProgressIndicator()
            }
        } else if (biometrics.isEmpty()) {
            Box(modifier = Modifier.fillMaxWidth().padding(32.dp), contentAlignment = Alignment.Center) {
                Text("No biometric data found", style = MaterialTheme.typography.bodyLarge)
            }
        } else {
            LazyColumn {
                items(biometrics) { biometric ->
                    BiometricCard(biometric = biometric)
                }
            }
        }
    }
}

@Composable
fun BiometricCard(biometric: Biometrics) {
    Card(modifier = Modifier.fillMaxWidth().padding(vertical = 4.dp)) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(modifier = Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                Text(
                    biometric.date,
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                if (biometric.weight != null) {
                    Text(
                        "${biometric.weight} ${biometric.weightUnits ?: ""}",
                        style = MaterialTheme.typography.titleMedium,
                        color = MaterialTheme.colorScheme.primary
                    )
                }
            }

            if (biometric.avgHr != null || biometric.highHr != null || biometric.lowHr != null) {
                Row(modifier = Modifier.fillMaxWidth().padding(top = 8.dp), horizontalArrangement = Arrangement.SpaceBetween) {
                    if (biometric.avgHr != null) Text("Avg HR: ${biometric.avgHr}")
                    if (biometric.highHr != null) Text("High: ${biometric.highHr}")
                    if (biometric.lowHr != null) Text("Low: ${biometric.lowHr}")
                }
            }

            if (!biometric.notes.isNullOrBlank()) {
                Text(
                    biometric.notes,
                    style = MaterialTheme.typography.bodyMedium,
                    modifier = Modifier.padding(top = 8.dp)
                )
            }
        }
    }
}
