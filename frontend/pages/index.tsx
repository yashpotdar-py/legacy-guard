import { useState } from 'react';
import {
  Box,
  Container,
  Heading,
  Text,
  VStack,
  HStack,
  Button,
  useToast,
  Progress,
  Select,
  Card,
  CardBody,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  StatArrow,
} from '@chakra-ui/react';
import { useDropzone } from 'react-dropzone';
import { FiUpload, FiFile, FiAlertCircle } from 'react-icons/fi';
import { useQuery, useMutation } from 'react-query';
import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export default function Home() {
  const [selectedLanguage, setSelectedLanguage] = useState('');
  const [projectName, setProjectName] = useState('');
  const [analysisId, setAnalysisId] = useState<string | null>(null);
  const toast = useToast();

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    accept: {
      'application/zip': ['.zip'],
      'application/x-tar': ['.tar', '.gz'],
    },
    maxFiles: 1,
    onDrop: async (acceptedFiles) => {
      const file = acceptedFiles[0];
      if (!file) return;

      const formData = new FormData();
      formData.append('project_file', file);
      formData.append('project_name', projectName || file.name);
      formData.append('language', selectedLanguage);

      try {
        const response = await axios.post(`${API_BASE_URL}/api/v1/analyze`, formData);
        setAnalysisId(response.data.project_id);
        toast({
          title: 'Analysis started',
          description: 'Your project is being analyzed. You can track the progress below.',
          status: 'success',
          duration: 5000,
          isClosable: true,
        });
      } catch (error) {
        toast({
          title: 'Error',
          description: 'Failed to start analysis. Please try again.',
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
      }
    },
  });

  const { data: analysis, isLoading } = useQuery(
    ['analysis', analysisId],
    async () => {
      if (!analysisId) return null;
      const response = await axios.get(`${API_BASE_URL}/api/v1/${analysisId}`);
      return response.data;
    },
    {
      enabled: !!analysisId,
      refetchInterval: (data) => (data?.status === 'running' ? 5000 : false),
    }
  );

  return (
    <Container maxW="container.xl" py={10}>
      <VStack spacing={8} align="stretch">
        <Heading textAlign="center" size="2xl">
          LegacyGuard
        </Heading>
        <Text textAlign="center" fontSize="xl" color="gray.600">
          Hybrid vulnerability detection for legacy codebases
        </Text>

        <Card>
          <CardBody>
            <VStack spacing={6}>
              <Box
                {...getRootProps()}
                w="100%"
                h="200px"
                border="2px dashed"
                borderColor={isDragActive ? 'blue.500' : 'gray.300'}
                borderRadius="lg"
                display="flex"
                alignItems="center"
                justifyContent="center"
                cursor="pointer"
                _hover={{ borderColor: 'blue.500' }}
              >
                <input {...getInputProps()} />
                <VStack spacing={4}>
                  <FiUpload size={40} />
                  <Text>
                    {isDragActive
                      ? 'Drop the project files here'
                      : 'Drag and drop your project files here, or click to select'}
                  </Text>
                </VStack>
              </Box>

              <HStack spacing={4} w="100%">
                <Select
                  placeholder="Select language"
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                >
                  <option value="cobol">COBOL</option>
                  <option value="c">C</option>
                  <option value="cpp">C++</option>
                  <option value="java">Java</option>
                  <option value="fortran">FORTRAN</option>
                </Select>

                <Button
                  colorScheme="blue"
                  leftIcon={<FiFile />}
                  onClick={() => document.querySelector('input[type="file"]')?.click()}
                >
                  Select Files
                </Button>
              </HStack>
            </VStack>
          </CardBody>
        </Card>

        {analysis && (
          <Card>
            <CardBody>
              <VStack spacing={6} align="stretch">
                <Heading size="md">Analysis Progress</Heading>
                
                <Progress
                  value={
                    (analysis.analyzed_files / analysis.total_files) * 100 || 0
                  }
                  colorScheme="blue"
                />

                <HStack spacing={8} justify="space-between">
                  <Stat>
                    <StatLabel>Files Analyzed</StatLabel>
                    <StatNumber>{analysis.analyzed_files}</StatNumber>
                    <StatHelpText>of {analysis.total_files}</StatHelpText>
                  </Stat>

                  <Stat>
                    <StatLabel>Vulnerabilities Found</StatLabel>
                    <StatNumber>{analysis.vulnerabilities_found}</StatNumber>
                    <StatHelpText>
                      <StatArrow type={analysis.vulnerabilities_found > 0 ? 'increase' : 'decrease'} />
                    </StatHelpText>
                  </Stat>

                  <Stat>
                    <StatLabel>Status</StatLabel>
                    <StatNumber color={analysis.status === 'completed' ? 'green.500' : 'blue.500'}>
                      {analysis.status}
                    </StatNumber>
                  </Stat>
                </HStack>

                {analysis.results.length > 0 && (
                  <VStack align="stretch" spacing={4}>
                    <Heading size="md">Vulnerabilities</Heading>
                    {analysis.results.map((result: any) => (
                      <Card key={result.id} variant="outline">
                        <CardBody>
                          <VStack align="stretch" spacing={2}>
                            <HStack justify="space-between">
                              <Text fontWeight="bold">{result.vulnerability_type}</Text>
                              <Text
                                color={
                                  result.severity === 'critical'
                                    ? 'red.500'
                                    : result.severity === 'high'
                                    ? 'orange.500'
                                    : 'yellow.500'
                                }
                              >
                                {result.severity}
                              </Text>
                            </HStack>
                            <Text>{result.description}</Text>
                            <Text fontSize="sm" color="gray.500">
                              File: {result.file_path}
                              {result.line_number && `:${result.line_number}`}
                            </Text>
                            <Text fontSize="sm" color="gray.500">
                              Recommendation: {result.recommendation}
                            </Text>
                          </VStack>
                        </CardBody>
                      </Card>
                    ))}
                  </VStack>
                )}
              </VStack>
            </CardBody>
          </Card>
        )}
      </VStack>
    </Container>
  );
} 