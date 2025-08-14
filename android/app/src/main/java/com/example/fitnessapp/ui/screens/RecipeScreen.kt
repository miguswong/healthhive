package com.example.fitnessapp.ui.screens

import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.padding
import androidx.compose.material3.Button
import androidx.compose.material3.Card
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Modifier
import androidx.compose.ui.unit.dp
import com.example.fitnessapp.data.ApiService
import com.example.fitnessapp.data.GenerateRecipeResponse
import com.example.fitnessapp.data.RecipeGenerationRequest
import androidx.compose.runtime.rememberCoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.launch
import kotlinx.coroutines.withContext

@Composable
fun RecipeScreen(userId: Int, onBack: () -> Unit) {
    val api = remember { ApiService.create("https://backend-45111119432.us-central1.run.app/") }
    val prompt = remember { mutableStateOf("") }
    val result = remember { mutableStateOf<GenerateRecipeResponse?>(null) }
    val loading = remember { mutableStateOf(false) }
    val error = remember { mutableStateOf<String?>(null) }

    val scope = rememberCoroutineScope()

    Column(modifier = Modifier.fillMaxSize().padding(16.dp)) {
        Text("Recipe Generator", style = MaterialTheme.typography.headlineSmall)
        OutlinedTextField(
            value = prompt.value,
            onValueChange = { prompt.value = it },
            label = { Text("Tell us what you want to eat") },
            modifier = Modifier.padding(top = 12.dp)
        )

        Button(onClick = {
            scope.launch {
                loading.value = true
                error.value = null
                try {
                    val res = withContext(Dispatchers.IO) {
                        api.generateRecipe(RecipeGenerationRequest(userId = userId, userDirections = prompt.value))
                    }
                    result.value = res
                } catch (e: Exception) {
                    error.value = e.message
                } finally {
                    loading.value = false
                }
            }
        }, modifier = Modifier.padding(top = 12.dp), enabled = !loading.value) {
            Text("Generate")
        }

        if (error.value != null) {
            Text(error.value!!, color = MaterialTheme.colorScheme.error, modifier = Modifier.padding(top = 8.dp))
        }

        result.value?.recipe?.let { r ->
            Text("${result.value?.message ?: ""}", modifier = Modifier.padding(top = 12.dp))
            Card(modifier = Modifier.padding(top = 12.dp)) {
                Column(modifier = Modifier.padding(12.dp)) {
                    Text(r.recipeName, style = MaterialTheme.typography.titleMedium)
                    if (!r.recipeType.isNullOrBlank()) Text("Type: ${r.recipeType}")
                    if (!r.ingredients.isNullOrBlank()) {
                        Text("Ingredients:")
                        Text(r.ingredients ?: "")
                    }
                    if (!r.instructions.isNullOrBlank()) {
                        Text("Instructions:")
                        Text(r.instructions ?: "")
                    }
                    Text("Calories: ${r.calories ?: 0}, Protein: ${r.protein ?: 0.0}g, Carbs: ${r.carbs ?: 0.0}g, Fat: ${r.fat ?: 0.0}g")
                }
            }
        }

        Button(onClick = onBack, modifier = Modifier.padding(top = 16.dp)) { Text("Back") }
    }
}

